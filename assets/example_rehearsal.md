# Example question list for rehearse.py (goes with example.md)

> Made-up questions for the made-up example sheet, written only to show the format. `rehearse.py` reads the `##` papers, the `###` sub-questions and the `卡:` / `自写:` / `注:` / `答案:` lines; everything else, like this note, is ignored.
> Run from the folder that holds both files: `python <skill>/scripts/rehearse.py example.md example_rehearsal.md --out rehearsal.md`

## Practice paper 1

### a) Design a network for a dental clinic with reception PCs, a shared printer and patient Wi-Fi, and justify your design.
卡: 设计题框架 ①–④ | [office devices] = the reception PCs | [192.168.10.0/24] = 192.168.20.0/24 | [shared devices] = the shared printer | [each user group] = staff and patients | [the remote-access VPN] = the dentists' VPN
答案: star topology; private addressing with DHCP; separate VLAN for patients; NAT and a firewall

### b) What risks remain in your design, and how would you address them?
卡: 设计题框架 ⑤⑥ | [the Wi-Fi network] = the patient Wi-Fi

### c) The clinic will back up patient files and hold video consultations. Compare TCP and UDP and say which protocol suits each service.
卡: TCP 与 UDP ③④⑥ | [file transfer] = the nightly backup | [video calls] = video consultations
自写: The clinic should therefore send backups over TCP, whereas video consultations should use UDP.

### d) Describe the handshake TCP uses before data flows, and how UDP differs.
卡: 三次握手
卡: TCP 与 UDP ③

## Practice paper 2

### a) How many usable hosts fit in a /26 subnet, and what are the network and broadcast addresses of 192.168.10.77/26?
卡: 子网划分 ②③
注: copy the table row for /26 as well

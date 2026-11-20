# Example answer-card cheatsheet master (excerpt)

> A made-up excerpt for an introductory Computer Networks course, written only to show the format — learn the shape, not the content.
> Everything before the "## 答题卡" line is not printed.

## 答题卡

{DESIGN} **★★★★ 〔A 答题〕 设计题框架 Network design framework**
Q: Design a network for [a small office] and justify it → ①–④ · What risks remain, and how to address them? → ⑤⑥ · [ ] = 换成题目里的数据
① Topology: [Twenty desktops and four printers] connect to an access switch in a star topology, so one failed cable affects only one device and the switch can be replaced without rewiring.
② Addressing: The office uses the private range [192.168.10.0/24] with DHCP for clients and static addresses for [the printers and the file server], leaving room for 254 hosts.
③ Segmentation: Separate VLANs for [staff, guests and printers] keep broadcast domains small and let the router's access control lists block guests from internal servers.
④ Internet access: A router performs NAT for the private addresses, and a firewall allows only outbound traffic plus [the company VPN] inbound.
⑤ 单点故障 One risk is a single point of failure at the router or switch; to address it, keep a spare device and back up its configuration.
⑥ 无线安全 One risk is unauthorised access over Wi-Fi; to address it, use WPA3 with separate guest credentials and change all default passwords.

**★★★★ 〔1 传输层〕 TCP 与 UDP TCP vs UDP**
Q: Differences between TCP and UDP? → ①–⑤ · When would you use which? → ⑥
① 面向连接 TCP is a connection-oriented transport protocol that delivers a reliable, ordered byte stream between two applications.
② 无连接 UDP is a connectionless transport protocol that sends independent datagrams without guaranteeing delivery or order.
③ 连接 TCP sets up a connection with a three-way handshake before sending data, whereas UDP sends immediately without any setup.
④ 可靠性 TCP retransmits lost segments and uses acknowledgements, flow control and congestion control, whereas UDP leaves loss handling to the application.
⑤ 开销 TCP has a header of at least 20 bytes and more latency, whereas UDP has an 8-byte header and lower latency.
⑥ 选择 Use TCP when every byte must arrive, e.g. web pages, email or file transfer; use UDP for time-sensitive traffic such as video calls, online games or DNS lookups.

{W2} **★★★ 三次握手 Three-way handshake** A TCP client sends SYN, the server answers SYN-ACK and the client replies ACK, after which both sides have agreed on initial sequence numbers and data can flow.

**★★★★ 〔2 网络层〕 子网划分 Subnetting**
Q: How many hosts fit in a given subnet? → ①②, table · What are the network and broadcast addresses? → ③
① 定义 A CIDR prefix such as /26 says how many leading bits of an IPv4 address identify the network; the remaining bits number the hosts.
② 主机数 A subnet with h host bits holds 2^h − 2 usable hosts, because the all-zeros address names the network and the all-ones address is the broadcast address.
③ 例子 For 192.168.10.77/26 the mask is 255.255.255.192, so the network address is 192.168.10.64 and the broadcast address is 192.168.10.127.

| Prefix | Mask | Usable hosts |
|---|---|---|
| /24 | 255.255.255.0 | 254 |
| /25 | 255.255.255.128 | 126 |
| /26 | 255.255.255.192 | 62 |
| /27 | 255.255.255.224 | 30 |

{W3} **★★ 网络诊断 ping and traceroute** `ping -c 4 example.com` tests reachability and round-trip time with ICMP echo requests, whereas `traceroute example.com` lists each router hop by sending packets with increasing TTL values.

{W3} **★★ 默认网关 Default gateway** A host sends packets for any address outside its own subnet to its default gateway, the router interface on its local network.

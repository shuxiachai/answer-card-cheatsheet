# Example answer-card cheatsheet master (excerpt)

> A made-up excerpt for an introductory Computer Networks course, written only to show the format — learn the shape, not the content.
> Everything before the "## 答题卡" line is not printed.
> 配色: 1=W1 2=W2 A=DESIGN
> The 〔A〕 framework card is here only because this made-up exam's marking guide gives every design answer the same sub-headings; without such headings, leave it out.

## 答题卡

**★★★★ 〔A 答题〕 设计题框架 design a network · topology · addressing · segmentation · Internet access · risks**
Q: Design a network for [a small office] and justify it → ①–④ · What risks remain, and how to address them? → ⑤⑥ · [ ] = 换成题目里的数据
① Topology: All [office devices] connect to an access switch in a star topology, so one failed cable affects only one device and the switch can be replaced without rewiring.
② Addressing: The network uses the private range [192.168.10.0/24] with DHCP for clients and static addresses for [shared devices], leaving room for 254 hosts.
③ Segmentation: Separate VLANs for [each user group] keep broadcast domains small and let the router's access control lists block untrusted groups from internal servers.
④ Internet access: A router performs NAT（地址转换）for the private addresses, and a firewall allows only outbound traffic plus [the remote-access VPN] inbound.
⑤ 单点故障 One risk is a single point of failure at the router or switch; to address it, keep a spare device and back up its configuration.
⑥ 无线安全 One risk is unauthorised access to [the Wi-Fi network]; to address it, use WPA3 with separate guest credentials and change all default passwords.

**★★★★ 〔1 传输层〕 TCP 与 UDP TCP vs UDP · reliability · handshake · latency · which protocol suits**
Q: Differences between TCP and UDP? → ①–⑤ · Which protocol suits a given application, and why? → ⑥
① 面向连接 TCP is a connection-oriented transport protocol that delivers a reliable, ordered byte stream between two applications.
② 无连接 UDP is a connectionless transport protocol that sends independent datagrams without guaranteeing delivery or order.
③ 连接 TCP sets up a connection with a three-way handshake before sending data, whereas UDP sends immediately without any setup.
④ 可靠性 TCP retransmits lost segments and uses acknowledgements, flow control and congestion control, whereas UDP leaves loss handling to the application.
⑤ 开销 TCP has a header of at least 20 bytes and more latency, whereas UDP has an 8-byte header and lower latency.
⑥ 选择 TCP suits [file transfer] because every byte must arrive in order, whereas UDP suits [video calls] because a late packet is useless and retransmitting it only adds delay.

{W1} **★★★ 三次握手 Three-way handshake** A TCP client sends SYN, the server answers SYN-ACK and the client replies ACK, after which both sides have agreed on initial sequence numbers and data can flow.

**★★★★ 〔2 网络层〕 子网划分 subnetting · CIDR · usable hosts · network and broadcast address**
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

{W2} **★★ 网络诊断 ping and traceroute** `ping -c 4 example.com` tests reachability and round-trip time with ICMP echo requests, whereas `traceroute example.com` lists each router hop by sending packets with increasing TTL（生存时间）values.

{W2} **★★ 默认网关 Default gateway** A host sends packets for any address outside its own subnet to its default gateway, the router interface on its local network.

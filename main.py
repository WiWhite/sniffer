import socket
import struct
import textwrap


def main():
    conn = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))

    while True:
        raw_data, addr = conn.recvfrom(65536)
        dst_mac, src_mac, eth_proto, data = ethernet_frame(raw_data)
        print('\nEthernet Frame: ')
        print(f'Destination: {dst_mac}, Source: '
              f'{src_mac}, Protocol: {eth_proto}')

        if eth_proto == 8:
            version, header_len, ttl, proto, src, target, data = \
                ipv4_packet(data)
            print(f'\tIPv4 Packets:\t\t'
                  f'Version: {version}, Header Length: {header_len}, '
                  f'TTL: {ttl}\n')
            print(f'\t\tProtocol: {proto}, Source: {src}, Target: {target}\n')

            if proto == 1:
                icmp_type, code, checksum, data = icmp_packet(data)
                form_mul_line = format_multi_line('\t\t\t', data)
                print(f'\tICMP Packet:\n\t\tType: {icmp_type}, Code: {code},'
                      f' Checksum: {checksum}\n\t\tData:\n{form_mul_line}')

            elif proto == 6:
                src_port, dst_port, sequence, acknowledgement, flag_urg, \
                flag_ack, flag_psh, flag_rst, flag_syn, flag_fin, data = \
                    tcp_segment(data)
                form_mul_line = format_multi_line('\t\t\t', data)
                print(f'\tTCP Segment:\n\t\tSource Port: {src_port}, '
                      f'Destination Port: {dst_port}\n\t\tSequence: {sequence}, '
                      f'Acknowledgement: {acknowledgement}\n\t\tFlags:\n\t\t\t'
                      f'URG: {flag_urg}, ACK: {flag_ack}, PSH: {flag_psh},'
                      f'RST: {flag_rst}, SYN: {flag_syn}, FIN: {flag_fin}\n\t\t'
                      f'Data:\n {form_mul_line}')

            elif proto == 17:
                src_port, dst_port, size, data = udp_segment(data)
                print(f'\tUDP Segment:\n\t\tSource Port: {src_port}, '
                      f'Destination Port: {dst_port}, Length: {size}')

            else:
                form_mul_line = format_multi_line('\t\t', data)
                print(f'\tData: {form_mul_line}')


def ethernet_frame(data):
    dst_mac, src_mac, proto = struct.unpack('! 6s 6s H', data[:14])
    return get_mac_addr(dst_mac), get_mac_addr(src_mac), socket.htons(
        proto), data[14:]


def get_mac_addr(bytes_addr):

    bytes_str = map('{:02x}'.format, bytes_addr)
    mac_addr = ':'.join(bytes_str).upper()

    return mac_addr


def ipv4_packet(data):

    ver_header_len = data[0]
    version = ver_header_len >> 4
    header_len = (ver_header_len & 15) * 4
    ttl, proto, src, target = struct.unpack('! 8x B B 2x 4s 4s', data[:20])

    return version, header_len, ttl, proto, ipv4(src), \
           ipv4(target), data[header_len:]


def ipv4(addr):
    return '.'.join(map(str, addr))


def icmp_packet(data):
    icmp_type, code, checksum = struct.unpack('! B B H', data[:4])
    return icmp_type, code, checksum, data[4:]


def tcp_segment(data):

    src_port, dst_port, sequence, acknowledgement, offset_reserved_flags = \
        struct.unpack('! H H L L H', data[:14])
    offset = (offset_reserved_flags >> 12) * 4
    flag_urg = (offset_reserved_flags & 32) >> 5
    flag_ack = (offset_reserved_flags & 16) >> 4
    flag_psh = (offset_reserved_flags & 8) >> 3
    flag_rst = (offset_reserved_flags & 4) >> 2
    flag_syn = (offset_reserved_flags & 2) >> 1
    flag_fin = offset_reserved_flags & 1

    return src_port, dst_port, sequence, acknowledgement, flag_urg, flag_ack, \
           flag_psh, flag_rst, flag_syn, flag_fin, data[offset:]


def udp_segment(data):
    src_port, dst_port, size = struct.unpack('! H H 2x H', data[:8])
    return src_port, dst_port, size, data[8:]


def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string, bytes):
        string = ''.join(r'\x{:02x}'.format(byte) for byte in string)
        if size % 2:
            size -= 1
    return '\n'.join(
        [f'{prefix}{line}' for line in textwrap.wrap(string, size)]
    )


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
 This script is used to configure port-forwarding for T-POT through Check Point:
 - Add TCP Services
 - Add UDP Services
 - Add port-forwarding NAT rule
 - Add NAT rule section
"""
import argparse
import logging
import sys

from cpapi import APIClient, APIClientArgs

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    """ """
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", default="admin")
    parser.add_argument("-p", "--password", default="Cpwins!1")
    parser.add_argument("-m", "--management", default="10.0.1.100")
    parser.add_argument("-d", "--domain", default="")
    parser.add_argument("-op", "--operation", default="add")

    parsed_args = parser.parse_args()

    client_args = APIClientArgs(server=parsed_args.management)
    with APIClient(client_args) as client:
        login = client.login(
            username=parsed_args.username,
            password=parsed_args.password,
            domain=parsed_args.domain,
        )
        if login.success:
            log.info(f"login succeeded to {parsed_args.domain}")
        else:
            log.error(login.error_message)
            sys.exit(1)

        # add tcp services
        tcp_ports = [
            22,
            23,
            25,
            110,
            143,
            389,
            1521,
            3306,
            6379,
            11211,
            631,
            80,
            8080,
            25565,
            2575,
            1433,
            1723,
            1883,
            3306,
            8081,
            9200,
            993,
            995,
            1080,
            5432,
            5900,
            21,
            5555,
            8443,
            102,
            502,
            1025,
            2404,
            10001,
            44818,
            47808,
            50100,
            11112,
            42,
            135,
            443,
            445,
        ]
        udp_ports = [5000, 161, 623, 19, 53, 123, 1900, 69, 53, 123, 161, 5060]

        if parsed_args.operation == "add":
            # add service groups
            add_service_group_response = client.api_call(
                "add-service-group",
                payload={"name": "tpot_services"},
            )

            if add_service_group_response.success:
                log.info(f"Added service group successfully")
            else:
                log.error(add_service_group_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing service group session")
            else:
                log.error(publish.error_message)

            # add TCP services
            for item in tcp_ports:
                add_tcp_services_response = client.api_call(
                    "add-service-tcp",
                    payload={
                        "name": f"tpot_tcp_{item}",
                        "port": f"{item}",
                        "keep-connections-open-after-policy-installation": "false",
                        "session-timeout": "0",
                        "match-for-any": "false",
                        "sync-connections-on-cluster": "true",
                        "aggressive-aging": {
                            "enable": "true",
                            "timeout": "360",
                            "use-default-timeout": "false",
                        },
                        "groups": ["tpot_services"],
                        "ignore-errors": "true",
                        "set-if-exists": "true",
                    },
                )

                if add_tcp_services_response.success:
                    log.info(f"Added TCP service {item} successfully")
                else:
                    log.error(add_tcp_services_response.error_message)

            # add UDP services
            for item in udp_ports:
                add_udp_services_response = client.api_call(
                    "add-service-udp",
                    payload={
                        "name": f"tpot_udp_{item}",
                        "port": f"{item}",
                        "keep-connections-open-after-policy-installation": "false",
                        "session-timeout": "0",
                        "match-for-any": "false",
                        "sync-connections-on-cluster": "true",
                        "aggressive-aging": {
                            "enable": "true",
                            "timeout": "360",
                            "use-default-timeout": "false",
                        },
                        "accept-replies": "false",
                        "groups": ["tpot_services"],
                        "ignore-errors": "true",
                        "set-if-exists": "true",
                    },
                )

                if add_udp_services_response.success:
                    log.info(f"Added UDP service {item} successfully")
                else:
                    log.error(add_udp_services_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing services session")
            else:
                log.error(publish.error_message)

            # add NAT section
            add_nat_section_response = client.api_call(
                "add-nat-section",
                payload={
                    "package": "Standard",
                    "name": "T-POT Rules",
                    "position": "top",
                },
            )

            if add_nat_section_response.success:
                log.info(f"Added NAT Section successfully")
            else:
                log.error(add_nat_section_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing NAT Section")
            else:
                log.error(publish.error_message)

            # add NAT rule for tpot port forwarding
            add_nat_rule_response = client.api_call(
                "add-nat-rule",
                payload={
                    "name": "T-POT",
                    "package": "Standard",
                    "position": {"top": "T-POT Rules"},
                    "comments": "tpot services",
                    "enabled": "true",
                    "install-on": ["hq_gw"],
                    "original-source": "Any",
                    "original-destination": "hq_gw",
                    "original-service": "tpot_services",
                    "translated-source": "Original",
                    "translated-destination": "host_10.0.4.70_hq_tpot",
                    "translated-service": "Original",
                },
            )

            if add_nat_rule_response.success:
                log.info(f"Added NAT rule successfully")
            else:
                log.error(add_nat_rule_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing NAT rules")
            else:
                log.error(publish.error_message)

        else:
            # Delete NAT section
            delete_nat_section_response = client.api_call(
                "delete-nat-section",
                payload={"package": "Standard", "name": "T-POT Rules"},
            )

            if delete_nat_section_response.success:
                log.info(f"Deleted NAT Section successfully")
            else:
                log.error(delete_nat_section_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing delete of NAT Section")
            else:
                log.error(publish.error_message)

            # delete NAT rule for tpot port forwarding
            delete_nat_rule_response = client.api_call(
                "delete-nat-rule",
                payload={
                    "name": "T-POT",
                    "package": "Standard",
                },
            )

            if delete_nat_rule_response.success:
                log.info(f"Deleted NAT rule successfully")
            else:
                log.error(delete_nat_rule_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing deleting NAT rules")
            else:
                log.error(publish.error_message)

            # delete service groups
            delete_service_group_response = client.api_call(
                "delete-service-group",
                payload={"name": "tpot_services"},
            )

            if delete_service_group_response.success:
                log.info(f"Deleted service group successfully")
            else:
                log.error(delete_service_group_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing service group deletion")
            else:
                log.error(publish.error_message)

            # delete TCP services
            for item in tcp_ports:
                delete_tcp_services_response = client.api_call(
                    "delete-service-tcp",
                    payload={
                        "name": f"tpot_tcp_{item}",
                    },
                )

                if delete_tcp_services_response.success:
                    log.info(f"Deleted service {item} successfully")
                else:
                    log.error(delete_tcp_services_response.error_message)

            # delete UDP services
            for item in udp_ports:
                delete_udp_services_response = client.api_call(
                    "delete-service-udp",
                    payload={
                        "name": f"tpot_udp_{item}",
                    },
                )

                if delete_udp_services_response.success:
                    log.info(f"Deleted service {item} successfully")
                else:
                    log.error(delete_udp_services_response.error_message)

            publish = client.api_call("publish", payload={})

            if publish.success:
                log.info("Publishing deleting services session")
            else:
                log.error(publish.error_message)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Remove those pesky AWS default VPCs (safely, with dry-run support).

Usage:
    python delete_default_vpcs.py --profile myawsprofile --dry-run
    python delete_default_vpcs.py --profile myawsprofile
"""

import boto3
import argparse
from botocore.exceptions import ClientError


def log(msg, level="INFO"):
    """Simple colored log output."""
    colors = {
        "INFO": "\033[94m",    # Blue
        "WARN": "\033[93m",    # Yellow
        "ERROR": "\033[91m",   # Red
        "SUCCESS": "\033[92m", # Green
    }
    reset = "\033[0m"
    print(f"{colors.get(level, '')}[{level}] {msg}{reset}")


def safe_call(func, **kwargs):
    """Call boto3 function safely and print meaningful errors."""
    try:
        return func(**kwargs)
    except ClientError as e:
        if e.response['Error']['Code'] == 'DryRunOperation':
            log("Dry-run successful (no changes made)", "SUCCESS")
        else:
            log(e.response['Error']['Message'], "ERROR")


def delete_igw(ec2, vpc_id, dry_run=False):
    """Detach and delete Internet Gateway."""
    igws = ec2.describe_internet_gateways(
        Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
    ).get('InternetGateways', [])

    for igw in igws:
        igw_id = igw['InternetGatewayId']
        log(f"Detaching and deleting IGW {igw_id} from {vpc_id}")
        safe_call(ec2.detach_internet_gateway, InternetGatewayId=igw_id, VpcId=vpc_id, DryRun=dry_run)
        safe_call(ec2.delete_internet_gateway, InternetGatewayId=igw_id, DryRun=dry_run)


def delete_subnets(ec2, vpc_id, dry_run=False):
    """Delete subnets."""
    subs = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]).get('Subnets', [])
    for sub in subs:
        log(f"Deleting subnet {sub['SubnetId']}")
        safe_call(ec2.delete_subnet, SubnetId=sub['SubnetId'], DryRun=dry_run)


def delete_route_tables(ec2, vpc_id, dry_run=False):
    """Delete non-main route tables."""
    rtbs = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]).get('RouteTables', [])
    for rtb in rtbs:
        if any(assoc.get('Main') for assoc in rtb.get('Associations', [])):
            continue
        log(f"Deleting route table {rtb['RouteTableId']}")
        safe_call(ec2.delete_route_table, RouteTableId=rtb['RouteTableId'], DryRun=dry_run)


def delete_acls(ec2, vpc_id, dry_run=False):
    """Delete non-default network ACLs."""
    acls = ec2.describe_network_acls(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]).get('NetworkAcls', [])
    for acl in acls:
        if acl['IsDefault']:
            continue
        log(f"Deleting network ACL {acl['NetworkAclId']}")
        safe_call(ec2.delete_network_acl, NetworkAclId=acl['NetworkAclId'], DryRun=dry_run)


def delete_security_groups(ec2, vpc_id, dry_run=False):
    """Delete non-default security groups."""
    sgps = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]).get('SecurityGroups', [])
    for sg in sgps:
        if sg['GroupName'] == 'default':
            continue
        log(f"Deleting security group {sg['GroupId']} ({sg['GroupName']})")
        safe_call(ec2.delete_security_group, GroupId=sg['GroupId'], DryRun=dry_run)


def delete_vpc(ec2, vpc_id, region, dry_run=False):
    """Delete the VPC."""
    log(f"Deleting VPC {vpc_id} in region {region}")
    safe_call(ec2.delete_vpc, VpcId=vpc_id, DryRun=dry_run)
    if not dry_run:
        log(f"VPC {vpc_id} deleted from {region}", "SUCCESS")


def get_regions(session):
    """Return all AWS regions."""
    ec2 = session.client('ec2', region_name='us-east-1')
    return [r['RegionName'] for r in ec2.describe_regions()['Regions']]


def has_attached_resources(ec2, vpc_id):
    """Check if the VPC still has resources."""
    eni = ec2.describe_network_interfaces(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]).get('NetworkInterfaces', [])
    return len(eni) > 0


def process_region(session, region, dry_run=False):
    """Handle cleanup in one region."""
    ec2 = session.client('ec2', region_name=region)
    attribs = ec2.describe_account_attributes(AttributeNames=['default-vpc'])['AccountAttributes']
    vpc_id = attribs[0]['AttributeValues'][0]['AttributeValue']

    if vpc_id == 'none':
        log(f"No default VPC in region {region}", "WARN")
        return

    if has_attached_resources(ec2, vpc_id):
        log(f"VPC {vpc_id} has existing resources in {region}. Skipping.", "WARN")
        return

    log(f"Processing default VPC {vpc_id} in {region} (dry-run={dry_run})")
    delete_igw(ec2, vpc_id, dry_run)
    delete_subnets(ec2, vpc_id, dry_run)
    delete_route_tables(ec2, vpc_id, dry_run)
    delete_acls(ec2, vpc_id, dry_run)
    delete_security_groups(ec2, vpc_id, dry_run)
    delete_vpc(ec2, vpc_id, region, dry_run)


def main(profile, dry_run):
    """Main execution flow."""
    session = boto3.Session(profile_name=profile)
    regions = get_regions(session)

    for region in regions:
        process_region(session, region, dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete AWS default VPCs safely (with dry-run option).")
    parser.add_argument("--profile", required=True, help="AWS CLI profile name")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without deleting anything")
    args = parser.parse_args()

    main(profile=args.profile, dry_run=args.dry_run)


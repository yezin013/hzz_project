from pymongo import MongoClient
import sys

try:
    print("Connecting to Primary via SSH Tunnel...")
    client = MongoClient("mongodb://root:pass123%23@localhost:27018/admin?authSource=admin&directConnection=true", serverSelectionTimeoutMS=5000)
    
    print("Fetching current Replica Set Config...")
    config = client.admin.command("replSetGetConfig")['config']
    
    print(f"\nCurrent Config Version: {config['version']}")
    print("\nCurrent Members:")
    for member in config['members']:
        print(f"  - {member['host']} (ID: {member['_id']})")
    
    # Find and update local node
    found = False
    for member in config['members']:
        if '100.95.123.56' in member['host']:
            print(f"\n✅ Found local node: {member['host']}")
            old_host = member['host']
            member['host'] = '100.95.123.56:27017'
            print(f"   Changed to: {member['host']}")
            found = True
            break
    
    if not found:
        print("\n❌ ERROR: Could not find member with IP 100.95.123.56")
        print("   Please check the member list above.")
        sys.exit(1)
    
    # Increment version
    config['version'] += 1
    print(f"\nNew Config Version: {config['version']}")
    
    # Apply reconfig
    print("\nApplying reconfig...")
    result = client.admin.command("replSetReconfig", config)
    print(f"✅ Reconfig successful: {result}")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

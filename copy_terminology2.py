import sys
import site
import json
import subprocess
import psycopg2
import uuid
import string
import secrets

def read_config():
    with open("terraform/common.json") as f:
        common_config = json.load(f)
    with open("terraform/tenants.json") as f:
        tenants_config = json.load(f)
    return common_config, tenants_config

def add_keyvault_secret(keyvault_name, secret_name, secret_value):
    # Generate a new random token if needed
    secret_exists = subprocess.run(
        ["az", "keyvault", "secret", "show", "--vault-name", keyvault_name, "--name", secret_name],
        capture_output=True, text=True)

    if secret_exists.stdout:
        # Update the secret if it exists
        subprocess.run(
            ["az", "keyvault", "secret", "set", "--vault-name", keyvault_name, "--name", secret_name, "--value", secret_value],
            capture_output=True)
        print(f"Secret {secret_name} has been updated in key vault: {keyvault_name}")
    else:
        # Create a new secret if it doesn't exist
        subprocess.run(
            ["az", "keyvault", "secret", "set", "--vault-name", keyvault_name, "--name", secret_name, "--value", secret_value],
            capture_output=True)
        print(f"Secret {secret_name} has been created in key vault: {keyvault_name}")

def copy_terminology(connection, tenant_config):
    secret_value = generate_random_token()
    command_text = f"""
        SELECT copy_terminology('{tenant_config["source"]}', '{tenant_config["name"]}',
        ARRAY{tenant_config["languages"]}, '{secret_value}');
    """
    try:
        with connection.cursor() as cur:
            cur.execute(command_text)
            connection.commit()
            print(f"Copied terminology for tenant: {tenant_config['name']}")
    except Exception as e:
        print(f"Error copying terminology for tenant {tenant_config['name']}: {str(e)}")

def generate_random_token(length=32):
    # Define characters to use for token generation
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def update_tenant_db():
    try:
        common_config, tenants_config = read_config()
        connection = psycopg2.connect(common_config['terminologydb']['connectionstring'])
        keyvault_name = common_config['terminologydb']['keyvultname']

        for tenant in tenants_config:
            tenant_config = tenant['tenantDB']['tenantInformation']

            # Generate token and add it to Key Vault
            secret_value = generate_random_token()
            add_keyvault_secret(keyvault_name, f"{tenant_config['identifier']}-token", secret_value)

            # Copy terminology to database
            copy_terminology(connection, tenant_config)

    except Exception as e:
        print(f"Error updating tenant database: {str(e)}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    update_tenant_db()

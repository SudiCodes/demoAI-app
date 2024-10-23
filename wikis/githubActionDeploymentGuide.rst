=========================================
Github Actions Deployment Steps
=========================================

-----------------------------------------
Configure on EC2
-----------------------------------------

1. Navigate to the home directory:

.. code-block:: bash

    $ cd ~
    $ pwd
    >> /home/ec2-user

   This ensures you are in the EC2 user’s home directory (`/home/ec2-user`) where configuration files and SSH keys are typically stored.

2. Move to the `.ssh` folder:

.. code-block:: bash

    cd .ssh
    $ ls
    >> authorized_keys

   The `.ssh` directory contains files related to SSH (Secure Shell) connections, including the `authorized_keys` file, which stores public keys allowed to access the server.

3. Generate SSH keys for GitHub Actions access:

.. code-block:: bash

    $ ssh-keygen -t rsa -b 4096 -C "Flask-App"

   This generates a new RSA key pair (public and private) for secure GitHub Actions access to the EC2 instance. 

   - When prompted to specify the file, save the key as `gitactions`.
   - Press Enter twice to skip setting a passphrase.
   - This will create two files: `gitactions` (private key) and `gitactions.pub` (public key).

   Example output:

.. code-block::

    Generating public/private rsa key pair.
    Enter file in which to save the key (/home/ec2-user/.ssh/id_rsa): gitactions
    Enter passphrase (empty for no passphrase):
    Enter same passphrase again:
    Your identification has been saved in gitactions
    Your public key has been saved in gitactions.pub

4. Add the public key to the `authorized_keys` file:

.. code-block:: bash

    $ cat gitactions.pub >> authorized_keys

   This appends the new public key to the `authorized_keys` file, allowing future SSH connections using the associated private key.

5. View the private key for later use:

.. code-block:: bash

    $ cat gitactions

   Copy the entire output (starting from `-----BEGIN OPENSSH PRIVATE KEY-----` to `-----END OPENSSH PRIVATE KEY-----`) and save it securely. You will need it later when configuring GitHub Actions.

-----------------------------------------
Configure on GitHub
-----------------------------------------

1. **Create a Personal Access Token (PAT) for authentication:**

   - Go to https://github.com/settings/tokens (Login if needed).
   - Click on "Generate new token" -> "Generate new token (classic)".
   - Add a descriptive note, and check the permissions for `repo` and `workflow`.
   - Generate the token and save it securely (you will not be able to view it again).

2. **Secret Management on GitHub:**

   - Navigate to the repository's settings.
   - In the left panel, open **Secrets and variables** -> **Actions**.
   - Click **New repository secret** and add the following secrets:

   - `HOST_NAME`: Your EC2 Public IP
   - `PAT`: Your GitHub Personal Access Token (from step 1)
   - `SSH_KEY`: The private key (`gitactions`) from EC2
   - `USER_NAME`: `ec2-user` (default username for Amazon Linux)

3. **Prepare GitHub Actions Workflow File:**

   - Go to the **Actions** tab in your repository.
   - Select **Set up a workflow yourself** and replace the content with the following:

.. code-block:: yaml

    name: Flask Deployment
    on:
      push:
        branches: [main]

    jobs:
      Deploy:
        name: Deploy to EC2
        runs-on: ubuntu-latest

        steps:
        - name: Deploy to EC2
          env:
            PRIVATE_KEY: ${{ secrets.SSH_KEY }}
            HOST_NAME: ${{ secrets.HOST_NAME }}
            USER_NAME: ${{ secrets.USER_NAME }}
            PAT: ${{ secrets.PAT }}  
          run: |
            echo "Step 1: Creating private key file"
            echo "$PRIVATE_KEY" > private_key
            chmod 600 private_key
            echo "Private key file created and permissions set."

            echo "Step 2: SSH into EC2 instance"
            ssh -o StrictHostKeyChecking=no -i private_key ${USER_NAME}@${HOST_NAME} << EOF
            echo "SSH connection successful"

            echo "Step 3: Navigating to the project directory"
            cd /home/ec2-user/demoAI-app || { echo "Directory not found"; exit 1; }

            echo "Step 4: Configuring Git credentials"
            git config --global credential.helper store
            echo "https://${PAT}:@github.com" > ~/.git-credentials

            echo "Step 5: Pulling the latest code from GitHub"
            git pull <YOUR_REPO_URL> || { echo "Git pull failed"; exit 1; }

            echo "Step 6: Restarting Gunicorn"
            sudo systemctl restart gunicorn || { echo "Failed to restart Gunicorn"; exit 1; }

            echo "Deployment completed successfully."
            EOF

4. **Commit and Push:**

   - Save and commit the `.github/workflows/main.yml` file.
   - Push any changes to the main branch of your repository.
   - Track the progress in the **Actions** tab.


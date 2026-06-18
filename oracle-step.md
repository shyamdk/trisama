# Deploy Trisama on Oracle Linux in OCI

This guide deploys the app from:

```bash
git@github.com:shyamdk/trisama.git
```

Target ports:

- Frontend: `3010`
- Backend API: `8010`
- Browser URL: `http://<RESERVED_PUBLIC_IP>:3010`
- API health URL: `http://<RESERVED_PUBLIC_IP>:8010/health`

This avoids OCI Load Balancer so the setup stays suitable for an Always Free-style deployment. Keep checking OCI Cost Analysis/Budgets after deployment.

## 1. OCI Network Checklist

Your instance must be in a public subnet with:

- A public IPv4 address.
- An internet gateway on the VCN.
- Route table sending internet traffic to the internet gateway.
- Ingress security rules for the app ports.

OCI documents that an internet-reachable instance needs a public subnet, public IP, internet gateway, route table, and security rules.

Add these ingress rules either in the subnet Security List or, preferably, in a Network Security Group attached to the instance VNIC:

| Source CIDR | Protocol | Destination port | Purpose |
| --- | --- | --- | --- |
| your home/office IP `/32` | TCP | 22 | SSH |
| `0.0.0.0/0` | TCP | 3010 | Web frontend |
| `0.0.0.0/0` | TCP | 8010 | API backend |

For better security later, replace `0.0.0.0/0` with only the networks you use. For first phone/tablet access, opening `3010` and `8010` publicly is the simplest path.

## 2. Reserve a Stable Public IP

OCI has two public IP types:

- Ephemeral: tied to the instance/VNIC lifetime.
- Reserved: persistent until you delete it; can be unassigned and reassigned.

Important: OCI documentation says an ephemeral public IP cannot be converted into a reserved public IP. Create a new reserved public IP, then assign it to the instance private IP.

Console steps:

1. OCI Console -> Networking -> IP Management -> Reserved Public IPs.
2. Click `Create Reserved Public IP`.
3. Name it something like `trisama-public-ip`.
4. Use Oracle's public IP pool unless you have BYOIP.
5. After it is created, assign it to the instance:
   - Compute -> Instances -> your instance.
   - Open `Attached VNICs`.
   - Open the primary VNIC.
   - Open `IPv4 Addresses`.
   - Select the primary private IP action menu.
   - Edit public IP / assign public IP.
   - Choose `Reserved public IP`.
   - Select `trisama-public-ip`.
6. If an ephemeral IP is already assigned, OCI may require you to unassign it before assigning the reserved one.
7. Keep the existing SSH session open while changing the IP. Open a second terminal and reconnect using the new reserved IP after the change.

Always Free caution:

- Do not create an OCI Load Balancer for this simple deployment; load balancers can add cost.
- Keep the reserved public IP assigned to the instance.
- In OCI Console, set a Budget/Alert and check Cost Analysis after creating the IP. OCI pricing can change, so confirm the console does not show billable networking resources.

## 3. SSH Into the Instance

Use the default Oracle Linux user, usually `opc`:

```bash
ssh opc@<RESERVED_PUBLIC_IP>
```

Run all following commands on the OCI machine.

## 4. Install System Packages

Update the OS and install base tools:

```bash
sudo dnf update -y
sudo dnf install -y git firewalld gcc gcc-c++ make openssl-devel bzip2-devel libffi-devel zlib-devel sqlite
```

Install Python 3.11 or newer:

```bash
sudo dnf install -y python3.11 python3.11-pip
python3.11 --version
```

If `python3.11` is not available on your image, check what Oracle Linux provides:

```bash
sudo dnf search python3.11
sudo dnf search python3.12
```

Use Python 3.11+ for this app because the backend code uses modern Python type syntax.

Install Node.js 20:

```bash
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs
node -v
npm -v
```

`node -v` should print `v20.x` or newer.

## 5. Clone the Repository

Create the app directory:

```bash
sudo mkdir -p /opt/trisama
sudo chown -R "$USER":"$USER" /opt/trisama
```

Test GitHub SSH access:

```bash
ssh -T git@github.com
```

If GitHub says permission denied, create a deploy key on the OCI machine:

```bash
ssh-keygen -t ed25519 -C "oci-trisama-deploy"
cat ~/.ssh/id_ed25519.pub
```

Copy the public key output. In GitHub:

1. Open repo `shyamdk/trisama`.
2. Settings -> Deploy keys.
3. Add deploy key.
4. Paste the public key.
5. Keep write access unchecked unless you need to push from the server.

Clone:

```bash
git clone git@github.com:shyamdk/trisama.git /opt/trisama
cd /opt/trisama
```

## 6. Create Server Environment File

Create `.env` on the OCI machine. Do not commit this file.

```bash
cd /opt/trisama
cat > .env <<'EOF'
OPENAI_API_KEY=replace_with_your_openai_key
OPENAI_FOOD_MODEL=gpt-4.1-mini
PLOS_CORS_ORIGIN_REGEX=https?://[^/]+:(3000|3010)
EOF
chmod 600 .env
```

For a custom domain later, add explicit origins:

```bash
PLOS_CORS_ORIGINS=https://your-domain.example,http://your-domain.example:3010
```

## 7. Install Backend

```bash
cd /opt/trisama
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Quick backend test:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8010
```

Open a second SSH terminal and run:

```bash
curl http://127.0.0.1:8010/health
```

Expected:

```json
{"status":"ok"}
```

Stop the test server with `Ctrl+C`.

## 8. Install Frontend

```bash
cd /opt/trisama/frontend
npm ci
npm run build
```

Quick frontend test:

```bash
cd /opt/trisama/frontend
npx next start -H 0.0.0.0 -p 3010
```

Open a second SSH terminal and run:

```bash
curl -I http://127.0.0.1:3010
```

Expected: `HTTP/1.1 200 OK`.

Stop the test frontend with `Ctrl+C`.

## 9. Open Oracle Linux Firewall Ports

OCI security rules allow traffic to reach the VM. The VM OS firewall must also allow the ports.

```bash
sudo systemctl enable --now firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-port=3010/tcp
sudo firewall-cmd --permanent --add-port=8010/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

## 10. Create systemd Services

Find your Linux username:

```bash
whoami
```

The examples below use `opc`. If your username is different, replace `opc`.

Create API service:

```bash
sudo tee /etc/systemd/system/trisama-api.service >/dev/null <<'EOF'
[Unit]
Description=Trisama FastAPI backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=opc
Group=opc
WorkingDirectory=/opt/trisama
EnvironmentFile=/opt/trisama/.env
ExecStart=/opt/trisama/.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8010
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Find `npx`:

```bash
command -v npx
```

It is usually `/usr/bin/npx`. If yours is different, update the `ExecStart` line below.

Create web service:

```bash
sudo tee /etc/systemd/system/trisama-web.service >/dev/null <<'EOF'
[Unit]
Description=Trisama Next.js frontend
After=network-online.target trisama-api.service
Wants=network-online.target

[Service]
Type=simple
User=opc
Group=opc
WorkingDirectory=/opt/trisama/frontend
Environment=NODE_ENV=production
ExecStart=/usr/bin/npx next start -H 0.0.0.0 -p 3010
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Start and enable both:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now trisama-api
sudo systemctl enable --now trisama-web
```

Check status:

```bash
sudo systemctl status trisama-api --no-pager
sudo systemctl status trisama-web --no-pager
```

Logs:

```bash
sudo journalctl -u trisama-api -f
sudo journalctl -u trisama-web -f
```

## 11. Browser Access

From your laptop or phone:

```text
http://<RESERVED_PUBLIC_IP>:3010
```

Backend health check:

```text
http://<RESERVED_PUBLIC_IP>:8010/health
```

The frontend code derives the API URL from the current browser hostname and port `8010`. That means if you open:

```text
http://<RESERVED_PUBLIC_IP>:3010
```

the browser calls:

```text
http://<RESERVED_PUBLIC_IP>:8010
```

Do not open the UI as `http://127.0.0.1:3010` from your phone or laptop. On those devices, `127.0.0.1` means the phone/laptop itself, not the OCI server.

## 12. Verify Food Analyze

On the OCI server:

```bash
curl -i -X POST http://127.0.0.1:8010/foods/analyze \
  -H 'Content-Type: application/json' \
  --data '{"meal_type":"Lunch","food_item":"boiled rice (200 gms), jackfruit seed sambar, veges salad bowl, Psyllium Whole Husk Isabgol (1 spoon)","notes":""}'
```

Expected:

- `HTTP/1.1 200 OK`
- JSON with `calories`, `quality_score`, `comments`, `ai_risk_flags`, and `ai_ingredients`.

If it fails:

- Check `.env` has `OPENAI_API_KEY`.
- Check backend logs: `sudo journalctl -u trisama-api -n 100 --no-pager`.
- Check outbound internet from OCI: `curl https://api.openai.com`.

## 13. Update Deployment Later

```bash
cd /opt/trisama
git pull

.venv/bin/pip install -r requirements.txt

cd /opt/trisama/frontend
npm ci
npm run build

sudo systemctl restart trisama-api
sudo systemctl restart trisama-web
```

Verify:

```bash
curl http://127.0.0.1:8010/health
curl -I http://127.0.0.1:3010
```

## 14. Backup SQLite Data

The app uses SQLite at:

```text
/opt/trisama/plos.db
```

Back it up before major deploys:

```bash
mkdir -p ~/trisama-backups
cp /opt/trisama/plos.db ~/trisama-backups/plos-$(date +%F-%H%M).db
```

Restore example:

```bash
sudo systemctl stop trisama-api
cp ~/trisama-backups/plos-YYYY-MM-DD-HHMM.db /opt/trisama/plos.db
sudo chown opc:opc /opt/trisama/plos.db
sudo systemctl start trisama-api
```

## 15. Troubleshooting

Check listeners:

```bash
sudo ss -lntp | grep -E ':3010|:8010'
```

Check local services:

```bash
curl http://127.0.0.1:8010/health
curl -I http://127.0.0.1:3010
```

If local works but browser does not:

1. Check OCI Security List / NSG ingress rules for `3010` and `8010`.
2. Check Oracle Linux firewall: `sudo firewall-cmd --list-all`.
3. Confirm you are using the reserved public IP, not a stale ephemeral IP.
4. Confirm services bind to `0.0.0.0`, not only `127.0.0.1`.

If login works but Analyze does not:

1. Open `http://<RESERVED_PUBLIC_IP>:8010/health` from the same browser/device.
2. Check `OPENAI_API_KEY` in `/opt/trisama/.env`.
3. Check `sudo journalctl -u trisama-api -n 100 --no-pager`.
4. Verify CORS if using a custom hostname. Add that hostname to `PLOS_CORS_ORIGINS`.

## References

- OCI Public IP Addresses: https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/managingpublicIPs.htm
- OCI Security Lists: https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm
- OCI Connecting to an Instance: https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/accessinginstance.htm
- OCI Price List: https://www.oracle.com/cloud/price-list/

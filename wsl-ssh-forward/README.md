# WSL SSH Forward

Forward SSH connections from Windows port **2222** to WSL2, with **auto-detection of WSL2 IP** (which changes on every reboot).

## Cara Pakai

### 1. Setup SSH di WSL

```bash
sudo apt update
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 2. Jalankan Script (Pertama Kali)

Klik kanan `wsl-ssh-forward.bat` → **Run as administrator**

Atau dari PowerShell Admin:

```powershell
.\wsl-ssh-forward.bat
```

### 3. Tes dari Windows

```powershell
ssh abdullaah@localhost -p 2222
```

### 4. Tes dari Laptop Lain (satu jaringan)

```bash
ssh abdullaah@<IP_WINDOWS> -p 2222
```

Cari IP Windows dengan `ipconfig` (biasanya 192.168.x.x).

## Setup Auto-start (Task Scheduler)

Agar otomatis jalan tiap Windows boot (**wajib** karena butuh Admin):

1. **Windows + R** → `taskschd.msc`
2. **Create Task** (bukan Basic Task)
3. Tab **General**:
   - Name: `WSL SSH Forward`
   - Check **Run with highest privileges**
   - Check **Run whether user is logged on or not**
4. Tab **Triggers** → **New**:
   - Begin the task: `At startup`
   - OK
5. Tab **Actions** → **New**:
   - Action: `Start a program`
   - Program: `G:\wsl\scripts\wsl-ssh-forward.bat`
   - (Sesuaikan path dengan lokasi file di PC kamu)
6. OK

## Catatan

- WSL2 menggunakan **NAT**, jadi IP internalnya (172.29.x.x) tidak bisa diakses langsung dari jaringan luar.
- Script ini membuat **portproxy** dari `0.0.0.0:2222` ke IP WSL saat ini.
- Firewall otomatis dibuka untuk port **2222/TCP**.
- IP WSL berubah tiap reboot — script ini auto-detect setiap kali dijalankan.

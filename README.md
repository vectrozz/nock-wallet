# 💰 Nockchain Wallet - Web Interface

A modern web-based wallet interface for Nockchain, built with Flask (backend) and Vite + Vanilla JS (frontend).

## 🌟 Features

- **Balance Management**: View all your notes with detailed information
- **Multi-Note Transactions**: Manually select notes or let the wallet auto-select them
- **Smart Sorting**: Sort notes by block height or amount (ascending/descending)
- **Transaction Flow**: Create, sign, and send transactions with confirmation steps
- **Key Management**: Export and import wallet keys
- **Real-time Updates**: Automatic balance refresh after transactions
- **Responsive UI**: Clean, modern interface with dark mode

## 🏗️ Architecture

```
nock-dev-wallet/
├── backend/          # Flask REST API
│   ├── app.py       # Main application
│   ├── .env         # Backend configuration
│   └── requirements.txt
├── frontend/         # Vite + Vanilla JS
│   ├── main.js      # Main application logic
│   ├── index.html   # UI structure
│   ├── style.css    # Tailwind CSS
│   └── .env         # Frontend configuration
└── README.md
```

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+** and npm
- **nockchain-wallet CLI** installed and configured
- Git

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/vectrozz/nock-wallet.git
cd nock-wallet
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python3 -m venv nock-env

# Activate virtual environment
source nock-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (optional)
cat > .env << EOF
FLASK_HOST=0.0.0.0
FLASK_PORT=5007
FLASK_DEBUG=True
EOF

# Run the Flask application
python3 app.py
```

The backend will start on `http://localhost:5007`

### 3. Frontend Setup

Open a **new terminal** (keep the backend running):

```bash
# Navigate to frontend directory
cd nock-wallet/frontend

# Install dependencies
npm install

# Create .env file (optional)
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:5007
EOF

# Run the development server
npm run dev
```

The frontend will start on `http://localhost:5173` (or another port if 5173 is busy)

## 🎯 Usage

### Viewing Balance

1. Click **"🔄 Update Balance"** to fetch your wallet notes
2. View total balance and individual notes
3. Click on any note to expand and see full details

### Sorting Notes

Use the sort buttons above the notes list:
- **Block Height**: Sort by blockchain block height
- **Amount**: Sort by note value
- Click the same button to toggle ascending/descending (arrow direction indicates order)

### Sending Transactions

#### Option 1: Auto-Select Notes
1. Click **"💸 Send Transaction"**
2. Enter recipient public key
3. Enter amount in Nock
4. Adjust fee if needed (default: 10 nick)
5. Click **"Create Transaction"**
6. Review transaction details
7. Click **"Sign & Send"**

#### Option 2: Manual Note Selection
1. Check the boxes next to notes you want to use
2. Click **"💸 Send Selected"**
3. The amount field will be pre-filled with (total selected - fee)
4. Enter recipient public key
5. Click **"Create Transaction"**
6. Review and confirm

### Managing Keys

- **Export Keys**: Click **"📤 Export Keys"** to download a backup
- **Import Keys**: Click **"📥 Import Keys"** and select a `.export` file

## 🔧 Configuration

### Backend (.env)

```env
FLASK_HOST=0.0.0.0          # Server host (0.0.0.0 for all interfaces)
FLASK_PORT=5007             # Server port
FLASK_DEBUG=True            # Debug mode (set to False in production)
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://192.168.1.108:5007  # Backend API URL
```

**Note**: Change the IP address to match your backend server location.

## 📡 API Endpoints

- `GET /api/balance` - Fetch wallet balance and notes
- `POST /api/create-transaction` - Create a new transaction
- `POST /api/sign-transaction` - Sign a transaction
- `POST /api/send-transaction` - Broadcast transaction to network
- `POST /api/show-transaction` - View transaction details
- `GET /api/export-keys` - Export wallet keys
- `POST /api/import-keys` - Import wallet keys

## 🛠️ Development

### Backend Development

```bash
cd backend
source nock-env/bin/activate
python3 app.py
```

The Flask app will auto-reload on code changes when `FLASK_DEBUG=True`.

### Frontend Development

```bash
cd frontend
npm run dev
```

Vite provides hot module replacement (HMR) for instant updates.

### Building for Production

```bash
cd frontend
npm run build
```

This creates optimized files in the `dist/` directory.

## 🔒 Security Notes

- Never commit `.env` files (they're in `.gitignore`)
- Keep your `keys.export` files secure and backed up
- Use strong fees to ensure transaction priority
- Always verify transaction details before signing

## 🐛 Troubleshooting

### Backend won't start
- Check if port 5007 is already in use
- Verify `nockchain-wallet` CLI is installed and in PATH
- Check Python virtual environment is activated

### Frontend can't connect to backend
- Verify backend is running
- Check `VITE_API_BASE_URL` in frontend `.env`
- Check CORS settings if accessing from different domain

### Transaction fails
- Ensure sufficient balance (amount + fee)
- Verify recipient address is valid
- Check `nockchain-wallet` CLI is working: `nockchain-wallet list-notes`

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for the Nockchain

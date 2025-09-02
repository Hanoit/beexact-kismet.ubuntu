#!/bin/bash
# install_dependencies_ubuntu.sh

echo "🐧 Installing BeExact Kismet Processor on Ubuntu"
echo "================================================"

# Clean problematic repositories
echo "🧹 Cleaning problematic repositories..."
sudo rm -f /etc/apt/sources.list.d/pgdg.list 2>/dev/null || true
sudo rm -f /etc/apt/sources.list.d/pgadmin4.list 2>/dev/null || true

# 1. Update system
echo "📦 Updating system..."
sudo apt update

# 2. Install basic development dependencies
echo "🔧 Installing basic development dependencies..."
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev

# 3. Install Cairo and GObject dependencies (correct names)
echo "🎨 Installing Cairo and GObject dependencies..."
sudo apt install -y \
    libcairo2-dev \
    libgirepository1.0-dev \
    gir1.2-gtk-3.0 \
    libglib2.0-dev

# 4. Install precompiled Python system packages
echo "📦 Installing precompiled Python packages..."
sudo apt install -y \
    python3-gi \
    python3-cairo \
    python3-psutil || echo "⚠️  python3-psutil not available, will install via pip"

# 5. Create virtual environment (optional)
echo "🐍 Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# 6. Update pip
pip install --upgrade pip

# 7. Install clean Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# 8. Clean previous builds and compile solution
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.spec.bak
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "📦 Installing PyInstaller..."
pip install pyinstaller

echo "🔨 Compiling Solution..."
pyinstaller main.spec

# Variables for absolute paths
PROJECT_DIR=$(pwd)

# Automatically detect executable name - IMPROVED
echo "🔍 Detecting build output..."
if [ -d "dist" ]; then
    EXECUTABLE_NAME=$(ls dist/ | head -n1)
    if [ -n "$EXECUTABLE_NAME" ] && [ -d "dist/$EXECUTABLE_NAME" ]; then
        echo "🎯 Found executable directory: $EXECUTABLE_NAME"
    else
        echo "❌ No valid executable directory found in dist/"
        ls -la dist/ 2>/dev/null
        exit 1
    fi
else
    echo "❌ dist/ directory not found!"
    exit 1
fi

echo "📋 Build Summary:"
if [ -d "dist/$EXECUTABLE_NAME" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable location: dist/$EXECUTABLE_NAME/"
    echo "🎯 Main executable: dist/$EXECUTABLE_NAME/$EXECUTABLE_NAME"
    echo "📊 Build size:"
    du -sh dist/$EXECUTABLE_NAME/ 2>/dev/null || echo "Build directory created"

    # 9. Copy .env to executable directory
    echo "📋 Copying configuration files..."
    if [ -f ".env" ]; then
        cp .env dist/$EXECUTABLE_NAME/
        echo "✅ .env file copied to executable directory"
    else
        echo "⚠️  .env file not found, creating template..."
        cat > dist/$EXECUTABLE_NAME/.env << 'ENV_EOF'
# BeExact Kismet Processor Configuration
WATCH_DIRECTORY=/opt/kismetFiles
OUT_DIRECTORY=/opt/kismetFiles
MACVENDOR_PLAN_TYPE=premium
MACVENDOR_REQUESTS_PER_SECOND=25
MACVENDOR_API_TIMEOUT=8.0
API_KEY_MACVENDOR=your_api_key_here
DB_PATH=kismet.db
LOG_LEVEL=INFO
ENV_EOF
        echo "📝 Template .env created in dist/$EXECUTABLE_NAME/"
    fi

    # 10. Create desktop application
    echo "🖥️  Creating desktop application..."
    
    # Create .desktop file
    cat > BeExact_Kismet_Processor.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=BeExact Kismet Processor
Comment=Kismet File Processing and MAC Vendor Analysis
GenericName=Kismet Processor
Keywords=kismet;mac;vendor;wifi;analysis;
Icon=$PROJECT_DIR/icon/export-csv-32.png
Exec=gnome-terminal --working-directory="$PROJECT_DIR/dist/$EXECUTABLE_NAME" --title="BeExact Kismet Processor" -- bash -c "./$EXECUTABLE_NAME; echo ''; echo 'Press Enter to close...'; read"
Path=$PROJECT_DIR/dist/$EXECUTABLE_NAME
Terminal=true
StartupNotify=true
Categories=Development;Utility;Network;
StartupWMClass=gnome-terminal
Actions=run-source;run-config;

[Desktop Action run-source]
Name=Run from Source
Exec=gnome-terminal --working-directory="$PROJECT_DIR" --title="Kismet Processor (Source)" -- bash -c "source .venv/bin/activate && python kismet_export.py; echo ''; echo 'Press Enter to close...'; read"

[Desktop Action run-config]
Name=Edit Configuration
Exec=gedit $PROJECT_DIR/dist/$EXECUTABLE_NAME/.env
EOF

    # Make executable
    chmod +x BeExact_Kismet_Processor.desktop

    # Create launcher scripts - FIXED
    echo "🚀 Creating launcher scripts..."
    
    # Script to run compiled version
    cat > run_kismet_compiled.sh << EOF
#!/bin/bash
echo "🚀 Starting BeExact Kismet Processor (Compiled)"
echo "=============================================="

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$SCRIPT_DIR"

if [ -d "dist/$EXECUTABLE_NAME" ]; then
    cd dist/$EXECUTABLE_NAME
    if [ -f "./$EXECUTABLE_NAME" ]; then
        echo "✅ Starting Kismet Processor..."
        ./$EXECUTABLE_NAME
    else
        echo "❌ Executable not found!"
        exit 1
    fi
else
    echo "❌ Build directory not found!"
    echo "📋 Please run: pyinstaller main.spec"
    exit 1
fi

echo ""
echo "📋 Kismet Processor finished."
read -p "Press Enter to close..."
EOF

    chmod +x run_kismet_compiled.sh

    # Script to run from source code
    cat > run_kismet_source.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting BeExact Kismet Processor (Source)"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

echo "✅ Starting Kismet Processor from source..."
python kismet_export.py

echo ""
echo "📋 Kismet Processor finished."
read -p "Press Enter to close..."
EOF

    chmod +x run_kismet_source.sh

    # 11. Install desktop application
    echo "📱 Installing desktop application..."
    
    # Copy to user applications
    mkdir -p ~/.local/share/applications
    cp BeExact_Kismet_Processor.desktop ~/.local/share/applications/
    
    # Update applications cache
    update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
    
    # Copy to desktop if it exists
    if [ -d "$HOME/Desktop" ]; then
        cp BeExact_Kismet_Processor.desktop "$HOME/Desktop/"
        echo "✅ Desktop shortcut created"
    fi
    
    echo "✅ Desktop application installed successfully!"

    echo ""
    echo "📋 Installation Summary:"
    echo "========================"
    echo "✅ Dependencies installed"
    echo "✅ Application compiled"
    echo "✅ Configuration files prepared"
    echo "✅ Desktop application created"
    echo "✅ Launcher scripts created"
    echo ""
    echo "🚀 Ways to run the application:"
    echo "1. 📱 Desktop App: Search for 'BeExact Kismet Processor' in applications"
    echo "2. 🖱️  Double-click: BeExact_Kismet_Processor.desktop"
    echo "3. 📜 Compiled: ./run_kismet_compiled.sh"
    echo "4. 🐍 Source: ./run_kismet_source.sh"
    echo "5. 💻 Terminal: cd dist/$EXECUTABLE_NAME && ./$EXECUTABLE_NAME"
    echo ""
    echo "⚙️  Configuration: Edit dist/$EXECUTABLE_NAME/.env"
    echo "📖 Documentation: README.md"

else
    echo "❌ Build failed!"
    echo "📋 Check the build logs above for errors"
    exit 1
fi

echo ""
echo "✅ Installation and setup completed successfully!"
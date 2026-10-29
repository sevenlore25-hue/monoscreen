#!/data/data/com.termux/files/usr/bin/sh
# Termux kurulum betiği: bagimlilik gerektirmez, sadece python ister.
set -e
if command -v pkg >/dev/null 2>&1; then
  pkg install -y python git
fi
pip install -e "$(dirname "$0")"
echo "Kuruldu. Deneme: python examples/demo.py"

# ccllrun Studio — build dell'app macOS nativa.
#
#   make            costruisce "ccllrun Studio.app"
#   make run        build + apre l'app
#   make serve      solo server (senza finestra), per sviluppo / LAN
#   make clean
#
# Approccio (launcher C + WKWebView + bundle) derivato da DStudio
# di Giuseppe Perrotta (BSD-3): https://github.com/sk8erboi17/DStudio

APP      := ccllrun Studio.app
BIN      := $(APP)/Contents/MacOS/ccllrun-studio
PYTHON   ?= $$HOME/.ccllrun/venv/bin/python

.PHONY: all run serve clean

all: $(BIN)

$(BIN): native/app.cc native/webview.h native/Info.plist native/AppIcon.icns server.py permtool.py web/index.html web/icon.svg web/mark.svg ../ccllrun ../proxy.py
	@mkdir -p "$(APP)/Contents/MacOS" "$(APP)/Contents/Resources/web"
	clang++ -x objective-c++ -std=c++17 -O2 \
	    native/app.cc -o "$(BIN)" \
	    -framework WebKit -framework Cocoa
	cp native/Info.plist "$(APP)/Contents/Info.plist"
	cp native/AppIcon.icns "$(APP)/Contents/Resources/AppIcon.icns"
	cp server.py "$(APP)/Contents/Resources/server.py"
	cp permtool.py "$(APP)/Contents/Resources/permtool.py"
	cp web/index.html web/icon.svg web/mark.svg "$(APP)/Contents/Resources/web/"
	cp ../ccllrun "$(APP)/Contents/Resources/ccllrun"
	cp ../proxy.py "$(APP)/Contents/Resources/proxy.py"
	chmod +x "$(APP)/Contents/Resources/ccllrun"
	@touch "$(APP)"
	@echo "✓ $(APP)"

run: all
	open "$(APP)"

serve:
	STUDIO_PORT=$${STUDIO_PORT:-8770} $(PYTHON) server.py

clean:
	rm -rf "$(APP)"

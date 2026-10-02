from pathlib import Path
import subprocess, re, struct, zlib, sys

repo = Path(sys.argv[1]).resolve()
qa = Path(sys.argv[2]).resolve()
qa.mkdir(exist_ok=True)

def png(file, width, height, color):
  def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
  raw = (b'\0' + bytes(color) * width) * height
  file.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))

png(qa / 'a.png', 640, 360, (30, 140, 80))
png(qa / 'b.png', 8000, 4500, (40, 80, 180))

def source(ref, file):
  return subprocess.check_output(['git', 'show', f'{ref}:{file}'], cwd=repo, text=True)

def function(text, name):
  match = re.search(r'^  function ' + name + r'\([\s\S]*?^  }', text, re.M)
  return match[0] if match else ''

for variant, ref in [('before', '821ae589059ffdadc970315f866c94b55d268af7'), ('after', '37d024fbea4e6a5e9ea9eb7fdf7add55a2e7020e')]:
  target = qa / variant
  target.mkdir(exist_ok=True)
  media = source(ref, 'shell/Ui/BackgroundMedia.qml').replace('import qs.Commons', 'import "."')
  (target / 'BackgroundMedia.qml').write_text(media)
  util = source(ref, 'shell/Commons/Util.qml')
  (target / 'Util.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject {\n' + function(util, 'fileUrl') + '\n' + function(util, 'isVideoPath') + '\n}\n')
  (target / 'qmldir').write_text('singleton Util 1.0 Util.qml\nBackgroundMedia 1.0 BackgroundMedia.qml\n')
  background = source(ref, 'shell/plugins/background/Background.qml')
  funcs = '\n'.join(function(background, name) for name in ['isVideo', 'setBackground', 'transitionBackground', 'applyPendingInstantBackground', 'requestNativeSize', 'probeNextSize'])
  handler = re.search(r'onExited: function\(exitCode\) \{([\s\S]*?)^    }', background, re.M)[1]
  template = '''import QtQuick
import QtQuick.Window
import "."
Window {
  id: window
  width: 640; height: 360; visible: true; color: "#ef00dd"
  Item {
    id: root
    anchors.fill: parent
    property string currentBackground: "APATH"
    property string displayedBackground: "APATH"
    property string pendingInstantBackground: ""
    property string incomingBackground: ""
    property string oldBackground: ""
    property string preparedBackground: ""
    property string lastTransitionPath: ""
    property var nativeSizes: ({"APATH": {width:640,height:360}})
    property var sizeQueue: []
    property bool finishingTransition: false
    property int backgroundVersion: 0
    property int revealStartedVersion: -1
    property real revealProgress: 1
    property string path: sizeProbe.path
    NATIVEHANDLER
    QtObject { id: preparedBackgroundTimer; function stop() {} }
    QtObject { id: revealAnimation; function stop() {} }
    QtObject { id: sizeProbeOut; property string text: "8000 4500" }
    QtObject { id: sizeProbe; property bool running: false; property string path: ""; property var command: []; onRunningChanged: if (running) probeTimer.restart() }
    function probeFinished(exitCode) { PROBEHANDLER }
    FUNCTIONS
    BackgroundMedia {
      id: base
      anchors.fill: parent
      path: root.displayedBackground
      RETENTION
      constrainDecode: true
      decodeSize: root.nativeSizes[root.displayedBackground] === undefined ? Qt.size(0,0) : Qt.size(640,360)
    }
    Timer { id: probeTimer; interval: 800; onTriggered: { sizeProbe.running = false; root.probeFinished(0) } }
    property int ticks: 0
    Timer {
      interval: 40; running: true; repeat: true
      onTriggered: {
        root.ticks++
        if (root.ticks === 12) root.setBackground("BPATH",true)
        if ([10,15,30,45].indexOf(root.ticks) !== -1) {
          var tag = root.ticks
          root.grabToImage(function(result) { result.saveToFile("OUTPATH/frame-" + tag + ".png"); console.log("CAPTURE " + tag + " displayed=" + root.displayedBackground + " ready=" + base.ready) })
        }
        if (root.ticks > 50) Qt.quit()
      }
    }
  }
}
'''
  template = template.replace('APATH', str(qa / 'a.png')).replace('BPATH', str(qa / 'b.png')).replace('OUTPATH', str(target))
  template = template.replace('NATIVEHANDLER', 'onNativeSizesChanged: applyPendingInstantBackground()' if variant == 'after' else '')
  template = template.replace('RETENTION', 'retainWhileLoading: true' if variant == 'after' else '')
  template = template.replace('FUNCTIONS', funcs).replace('PROBEHANDLER', handler)
  (target / 'fixture.qml').write_text(template)

print(qa)

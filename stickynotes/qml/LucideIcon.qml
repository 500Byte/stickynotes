import QtQuick
import QtQuick.Effects

Item {
    id: root

    property url source: ""
    property color color: "#1c1b1f"
    property real size: 16

    width: size
    height: size

    Image {
        id: img
        anchors.fill: parent
        source: root.source
        sourceSize.width: root.size * 2
        sourceSize.height: root.size * 2
        fillMode: Image.PreserveAspectFit
        visible: false
    }

    MultiEffect {
        anchors.fill: img
        source: img
        colorization: 1.0
        colorizationColor: root.color
    }
}

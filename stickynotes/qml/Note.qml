import QtQuick
import QtQuick.Controls
import QtQuick.Window

Window {
    id: win

    required property int index
    required property string noteId
    required property string noteText
    required property string noteColor
    required property int noteW
    required property int noteH

    property bool ready: false

    visible: true
    title: "StickyNote"
    color: "transparent"
    flags: Qt.Window | Qt.FramelessWindowHint
    minimumWidth: 160
    minimumHeight: 120
    width: 280
    height: 280

    Component.onCompleted: {
        width = noteW
        height = noteH
        ready = true
    }
    onWidthChanged: if (ready) sizeTimer.restart()
    onHeightChanged: if (ready) sizeTimer.restart()

    Timer {
        id: sizeTimer
        interval: 300
        onTriggered: notesModel.setSize(win.index, win.width, win.height)
    }

    readonly property color ink: "#1c1b1f"

    Rectangle {
        anchors.fill: parent
        color: win.noteColor

        Rectangle {
            id: bar
            width: parent.width
            height: 32
            color: Qt.darker(win.noteColor, 1.08)

            DragHandler {
                target: null
                onActiveChanged: if (active) win.startSystemMove()
            }

            Row {
                anchors.left: parent.left
                anchors.leftMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6

                Text {
                    text: "＋"
                    font.pixelSize: 18
                    color: win.ink
                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -4
                        cursorShape: Qt.PointingHandCursor
                        onClicked: notesModel.addNote()
                    }
                }

                Repeater {
                    model: noteColors
                    Rectangle {
                        required property string modelData
                        width: 14
                        height: 14
                        radius: 7
                        color: modelData
                        border.width: 1
                        border.color: Qt.darker(modelData, 1.3)
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: notesModel.setColor(win.index, parent.modelData)
                        }
                    }
                }
            }

            Text {
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                text: "✕"
                font.pixelSize: 14
                color: win.ink
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -6
                    cursorShape: Qt.PointingHandCursor
                    onClicked: notesModel.removeNote(win.index)
                }
            }
        }

        ScrollView {
            anchors.top: bar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 8

            TextArea {
                text: win.noteText
                color: win.ink
                selectionColor: Qt.darker(win.noteColor, 1.4)
                selectedTextColor: "white"
                wrapMode: TextEdit.Wrap
                font.pixelSize: 15
                background: null
                placeholderText: "Escribe una nota…"
                placeholderTextColor: Qt.rgba(0, 0, 0, 0.4)
                onTextChanged: if (activeFocus) notesModel.setText(win.index, text)
            }
        }

        MouseArea {
            width: 20
            height: 20
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            cursorShape: Qt.SizeFDiagCursor
            onPressed: win.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
        }
    }
}

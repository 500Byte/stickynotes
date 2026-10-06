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
    required property bool noteVisible
    required property string noteMode

    property bool ready: false

    visible: win.noteVisible
    title: "StickyNote"
    color: "transparent"
    flags: {
        let f = Qt.Window | Qt.FramelessWindowHint
        if (win.noteMode === "top") {
            f |= Qt.WindowStaysOnTopHint
        } else if (win.noteMode === "desktop") {
            f |= Qt.WindowStaysOnBottomHint
        }
        return f
    }
    minimumWidth: 160
    minimumHeight: 120
    width: 280
    height: 280

    onClosing: notesModel.removeNote(win.index)

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

    function cycleMode() {
        var nextMode = "normal"
        if (win.noteMode === "normal") {
            nextMode = "top"
        } else if (win.noteMode === "top") {
            nextMode = "desktop"
        } else {
            nextMode = "normal"
        }
        notesModel.setMode(win.index, nextMode)
    }

    function toggleChecklist() {
        var curPos = textArea.cursorPosition
        var t = textArea.text
        var lineStart = curPos > 0 ? t.lastIndexOf("\n", curPos - 1) + 1 : 0
        var nextNewline = t.indexOf("\n", curPos)
        var lineEnd = nextNewline === -1 ? t.length : nextNewline
        var line = t.substring(lineStart, lineEnd)

        var newLine = ""
        var diff = 0

        if (line.startsWith("[ ] ")) {
            newLine = "[x] " + line.substring(4)
            diff = 0
        } else if (line.startsWith("[x] ")) {
            newLine = "[ ] " + line.substring(4)
            diff = 0
        } else if (line.startsWith("[X] ")) {
            newLine = "[ ] " + line.substring(4)
            diff = 0
        } else if (line.startsWith("- [ ] ")) {
            newLine = "- [x] " + line.substring(6)
            diff = 0
        } else if (line.startsWith("- [x] ") || line.startsWith("- [X] ")) {
            newLine = "- [ ] " + line.substring(6)
            diff = 0
        } else if (line.startsWith("[] ")) {
            newLine = "[ ] " + line.substring(3)
            diff = 1
        } else {
            newLine = "[ ] " + line
            diff = 4
        }

        textArea.text = t.substring(0, lineStart) + newLine + t.substring(lineEnd)
        textArea.cursorPosition = Math.min(textArea.text.length, curPos + diff)
        notesModel.setText(win.index, textArea.text)
    }

    Shortcut {
        id: scNew
        objectName: "shortcutNew"
        sequence: "Ctrl+N"
        onActivated: notesModel.addNote()
    }

    Shortcut {
        id: scClose
        objectName: "shortcutClose"
        sequence: "Ctrl+W"
        onActivated: notesModel.removeNote(win.index)
    }

    Shortcut {
        id: scDelete
        objectName: "shortcutDelete"
        sequence: "Ctrl+Shift+D"
        onActivated: notesModel.deleteNote(win.index)
    }

    Shortcut {
        id: scCycleMode
        objectName: "shortcutCycleMode"
        sequence: "Ctrl+T"
        onActivated: win.cycleMode()
    }

    Shortcut {
        id: scEscape
        objectName: "shortcutEscape"
        sequence: "Escape"
        onActivated: textArea.focus = false
    }

    Shortcut {
        id: scChecklist
        objectName: "shortcutChecklist"
        sequence: "Ctrl+Shift+C"
        onActivated: win.toggleChecklist()
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

            Row {
                id: leftRow
                anchors.left: parent.left
                anchors.leftMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6

                Rectangle {
                    id: addBtn
                    width: 24
                    height: 24
                    radius: 4
                    color: addMa.containsMouse ? Qt.rgba(0, 0, 0, 0.08) : "transparent"
                    anchors.verticalCenter: parent.verticalCenter
                    ToolTip.visible: addMa.containsMouse
                    ToolTip.text: "Nueva nota"
                    ToolTip.delay: 400

                    LucideIcon {
                        anchors.centerIn: parent
                        source: "icons/plus.svg"
                        size: 15
                        color: win.ink
                    }

                    MouseArea {
                        id: addMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: notesModel.addNote()
                    }
                }

                Rectangle {
                    id: modeBtn
                    width: 24
                    height: 24
                    radius: 4
                    color: modeMa.containsMouse ? Qt.rgba(0, 0, 0, 0.08) : "transparent"
                    anchors.verticalCenter: parent.verticalCenter
                    ToolTip.visible: modeMa.containsMouse
                    ToolTip.text: win.noteMode === "top" ? "Top / Sobre todo" : (win.noteMode === "desktop" ? "Desktop / Pegado al fondo" : "Normal / Flotante normal")
                    ToolTip.delay: 400

                    LucideIcon {
                        anchors.centerIn: parent
                        source: win.noteMode === "top" ? "icons/pin.svg" : (win.noteMode === "desktop" ? "icons/monitor.svg" : "icons/app-window.svg")
                        size: 14
                        color: win.ink
                    }

                    MouseArea {
                        id: modeMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: win.cycleMode()
                    }
                }
            }

            Item {
                id: dragArea
                anchors.left: leftRow.right
                anchors.right: rightRow.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom

                DragHandler {
                    target: null
                    onActiveChanged: if (active) win.startSystemMove()
                }
            }

            Row {
                id: rightRow
                anchors.right: parent.right
                anchors.rightMargin: 8
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6

                Rectangle {
                    id: menuBtn
                    width: 24
                    height: 24
                    radius: 4
                    color: (menuMa.containsMouse || menuPopup.visible) ? Qt.rgba(0, 0, 0, 0.08) : "transparent"
                    anchors.verticalCenter: parent.verticalCenter
                    ToolTip.visible: menuMa.containsMouse && !menuPopup.visible
                    ToolTip.text: "Opciones de nota"
                    ToolTip.delay: 400

                    LucideIcon {
                        anchors.centerIn: parent
                        source: "icons/more-horizontal.svg"
                        size: 15
                        color: win.ink
                    }

                    MouseArea {
                        id: menuMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: menuPopup.visible ? menuPopup.close() : menuPopup.open()
                    }
                }

                Rectangle {
                    id: closeBtn
                    width: 24
                    height: 24
                    radius: 4
                    color: closeMa.containsMouse ? Qt.rgba(0, 0, 0, 0.08) : "transparent"
                    anchors.verticalCenter: parent.verticalCenter
                    ToolTip.visible: closeMa.containsMouse
                    ToolTip.text: "Cerrar nota (ocultar a bandeja)"
                    ToolTip.delay: 400

                    LucideIcon {
                        anchors.centerIn: parent
                        source: "icons/x.svg"
                        size: 14
                        color: win.ink
                    }

                    MouseArea {
                        id: closeMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: notesModel.removeNote(win.index)
                    }
                }
            }

            Popup {
                id: menuPopup
                x: parent.width - width - 8
                y: parent.height + 4
                padding: 10
                closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                background: Rectangle {
                    color: "#ffffff"
                    radius: 8
                    border.color: "#d0d0d0"
                    border.width: 1
                }

                contentItem: Column {
                    spacing: 8

                    Grid {
                        columns: 4
                        spacing: 8
                        anchors.horizontalCenter: parent.horizontalCenter

                        Repeater {
                            model: noteColors
                            Rectangle {
                                required property string modelData
                                width: 20
                                height: 20
                                radius: 10
                                color: modelData
                                border.width: win.noteColor.toLowerCase() === modelData.toLowerCase() ? 2 : 1
                                border.color: win.noteColor.toLowerCase() === modelData.toLowerCase() ? win.ink : Qt.darker(modelData, 1.3)
                                scale: colorMa.containsMouse ? 1.15 : 1.0
                                Behavior on scale { NumberAnimation { duration: 100 } }

                                MouseArea {
                                    id: colorMa
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: notesModel.setColor(win.index, parent.modelData)
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        height: 1
                        color: "#e8e8e8"
                    }

                    Rectangle {
                        id: deleteBtn
                        width: parent.width
                        height: 28
                        radius: 4
                        color: delMa.containsMouse ? "#ffebee" : "transparent"

                        Row {
                            anchors.centerIn: parent
                            spacing: 6

                            LucideIcon {
                                source: "icons/trash-2.svg"
                                size: 14
                                color: delMa.containsMouse ? "#c62828" : win.ink
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: "Eliminar nota"
                                font.pixelSize: 12
                                color: delMa.containsMouse ? "#c62828" : win.ink
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        MouseArea {
                            id: delMa
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                menuPopup.close()
                                notesModel.deleteNote(win.index)
                            }
                        }
                    }
                }
            }
        }

        ScrollView {
            anchors.top: bar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 8
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            TextArea {
                id: textArea
                objectName: "noteTextArea"
                text: win.noteText
                color: win.ink
                selectionColor: Qt.darker(win.noteColor, 1.4)
                selectedTextColor: "white"
                wrapMode: TextEdit.Wrap
                font.pixelSize: 15
                background: null
                placeholderText: "Escribe una nota…"
                placeholderTextColor: Qt.rgba(0, 0, 0, 0.4)
                rightPadding: 16
                bottomPadding: 16
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

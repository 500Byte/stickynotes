import QtQml

QtObject {
    property Instantiator notes: Instantiator {
        model: notesModel
        delegate: Note {}
    }
}

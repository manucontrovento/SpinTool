# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/manu/Sviluppo/SpinTool/superboucle/playlist_ui.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(320, 335)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/icons/icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.playlistList = QtWidgets.QListWidget(Dialog)
        self.playlistList.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.playlistList.setSizeIncrement(QtCore.QSize(100, 100))
        self.playlistList.setMovement(QtWidgets.QListView.Static)
        self.playlistList.setResizeMode(QtWidgets.QListView.Adjust)
        self.playlistList.setObjectName("playlistList")
        self.horizontalLayout.addWidget(self.playlistList)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.loadSongBtn = QtWidgets.QPushButton(Dialog)
        self.loadSongBtn.setObjectName("loadSongBtn")
        self.verticalLayout_3.addWidget(self.loadSongBtn)
        self.addSongsBtn = QtWidgets.QPushButton(Dialog)
        self.addSongsBtn.setObjectName("addSongsBtn")
        self.verticalLayout_3.addWidget(self.addSongsBtn)
        self.removeSongBtn = QtWidgets.QPushButton(Dialog)
        self.removeSongBtn.setObjectName("removeSongBtn")
        self.verticalLayout_3.addWidget(self.removeSongBtn)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.loadPlaylistBtn = QtWidgets.QPushButton(Dialog)
        self.loadPlaylistBtn.setObjectName("loadPlaylistBtn")
        self.verticalLayout_3.addWidget(self.loadPlaylistBtn)
        self.savePlaylistBtn = QtWidgets.QPushButton(Dialog)
        self.savePlaylistBtn.setObjectName("savePlaylistBtn")
        self.verticalLayout_3.addWidget(self.savePlaylistBtn)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.cBoxBigFonts = QtWidgets.QCheckBox(Dialog)
        self.cBoxBigFonts.setObjectName("cBoxBigFonts")
        self.gridLayout.addWidget(self.cBoxBigFonts, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Playlist"))
        self.loadSongBtn.setText(_translate("Dialog", "Load Song"))
        self.addSongsBtn.setText(_translate("Dialog", "Add Songs"))
        self.removeSongBtn.setText(_translate("Dialog", "Remove Song"))
        self.loadPlaylistBtn.setText(_translate("Dialog", "Import Playlist"))
        self.savePlaylistBtn.setText(_translate("Dialog", "Export Playlist"))
        self.cBoxBigFonts.setText(_translate("Dialog", "Use custom font size"))
import gui_rc

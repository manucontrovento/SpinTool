from PyQt5.QtWidgets import QDialog, QAbstractItemView, QListWidgetItem, QFrame, QMessageBox, QInputDialog, QLineEdit
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QSize
from superboucle.scene_manager_ui import Ui_Dialog
from superboucle.add_scene import AddSceneDialog
from superboucle.clip import load_song_from_file
from superboucle.preferences import Preferences
import settings

def getScenes(file_names):
    r = []
    for f in file_names:
        try:
            r.append(load_song_from_file(f))
        except Exception as e:
            print("could not load File {}.\nError: {}".format(f, e))
    return r


class SceneManager(QDialog, Ui_Dialog):
    ITEM_IT_ROLE = 100

    def __init__(self, parent):
        super(SceneManager, self).__init__(parent)
        self.select_scene = False
        self.last_item = None
        self.gui = parent
        self.setupUi(self)
        self.updateList()
        self.removeScenesBtn.clicked.connect(self.onRemove)
        self.addScenesBtn.clicked.connect(self.onAddScene)
        self.loadScenesBtn.clicked.connect(self.onLoadScene)
        self.renameSceneBtn.clicked.connect(self.onRename)
        self.scenelistList.itemDoubleClicked.connect(self.onSceneDoubleClick)
        self.scenelistList.setDragDropMode(QAbstractItemView.InternalMove)
        self.scenelistList.model().rowsMoved.connect(self.onMoveRows)
        self.scenelistList.currentItemChanged.connect(self.onCurrentItemChanged)
        self.setInitialSceneBtn.clicked.connect(self.onSetInitial)
        self.gui.songLoad.connect(self.updateList)
        self.initPreview()
        self.geometry = settings.scenes_geometry
        self.cBoxBigFonts.setChecked(settings.use_big_fonts_scenes)
        self.cBoxBigFonts.stateChanged.connect(self.onBigFonts)            
 
        if self.geometry:
            self.restoreGeometry(self.geometry)   
        
        if self.isVisible() == False:
            self.show()
        
        self.useBigFonts(settings.use_big_fonts_scenes)


    def selectItem(self, index):
        s_item = self.scenelistList.item(index)
        self.scenelistList.setCurrentItem(s_item)
        self.updatePreview(s_item) 
        

    def updateList(self):
        self.scenelistList.clear()
        for i, scene in enumerate(self.gui.song.scenes):
            item = QListWidgetItem('{}. {}'.format(i + 1, scene))
            item.setData(1, scene)
            item.setData(self.ITEM_IT_ROLE, i)
            if self.gui.song.initial_scene == scene:
                item.setBackground(QColor('red'))
            self.scenelistList.addItem(item)
            self.last_item = item
        
        if self.select_scene == True:
            self.scenelistList.setCurrentItem(self.last_item)
            self.updatePreview(self.last_item)            
            
        anyScenes = bool(self.gui.song.scenes)
        self.loadScenesBtn.setEnabled(anyScenes)
        self.removeScenesBtn.setEnabled(anyScenes)
        self.renameSceneBtn.setEnabled(anyScenes)
        
        if self.select_scene == False:
            self.initPreview()
        else:
            self.select_scene = False

    def initPreview(self):
        self.previewcells = [[None for y in range(self.gui.song.height)]
                             for x in range(self.gui.song.width)]

        for i in reversed(range(self.preview.count())):
            self.preview.itemAt(i).widget().close()
            self.preview.itemAt(i).widget().setParent(None)

        for y in range(self.gui.song.height):
            for x in range(self.gui.song.width):
                self.previewcells[x][y] = QFrame(self)
                self.previewcells[x][y].setMinimumSize(QSize(10, 10))
                self.previewcells[x][y].setStyleSheet("background-color: rgb(217, 217, 217);")
                self.preview.addWidget(self.previewcells[x][y], y, x, 1, 1)

    def _getSceneName(self, item):
        return list(self.gui.song.scenes.keys())[item.data(self.ITEM_IT_ROLE)]

    def onRemove(self):
        response = QMessageBox.question(self, "Delete Scene?", "Are you sure you want to delete this scene?")
        if response == QMessageBox.No:
            return

        item = self.scenelistList.currentItem()
        if item:
            self.gui.song.removeScene(self._getSceneName(item))
            self.updateList()

    def onMoveRows(self, sourceParent, sourceStart, sourceEnd,
                   destinationParent, destinationRow):
        l = self.gui.song.scenes
        k, v = list(l.items())[sourceStart]
        del l[k]
        destinationRow -= destinationRow > sourceStart
        l.insert(k, v, destinationRow)
        self.updateList()

    def onBigFonts(self):
        settings.use_big_fonts_scenes = self.cBoxBigFonts.isChecked()
        self.useBigFonts(settings.use_big_fonts_scenes)

    def onAddedScene(self):
        self.select_scene = True
        self.updateList()

    def onAddScene(self):
        AddSceneDialog(self.gui, callback=self.onAddedScene)

    def onRename(self):
        item = self.scenelistList.currentItem()
        if item:
            print("item!")
            currentName = self._getSceneName(item)
            print("currentName" + str(currentName))
            newName, okPressed = QInputDialog.getText(self, "Scene rename", "Enter scene new name:", QLineEdit.Normal, currentName)
            
            if okPressed and newName.strip() != '':
                if newName == currentName:
                    return
                    
                self.gui.song.renameScene(currentName, newName)
                self.updateList()

    def onSetInitial(self):
        item = self.scenelistList.currentItem()
        if item:
            self.gui.song.initial_scene = self._getSceneName(item)
            self.updateList()

    def onLoadScene(self):
        item = self.scenelistList.currentItem()
        if item:
            self.loadScene(self._getSceneName(item))
            self.gui.update()

    def onSceneDoubleClick(self, item):
        self.loadScene(self._getSceneName(item))
        self.gui.update()

    def updatePreview(self, item):
        if item is not None:
            scene = self.gui.song.getSceneDesc(item.data(1))
            for x in range(len(scene)):
                line = scene[x]
                for y in range(len(line)):
                    cell = self.previewcells[x][y]
                    if line[y] is None:
                        cell.setStyleSheet("background-color: rgb(217, 217, 217);")
                    elif line[y]:
                        cell.setStyleSheet("background-color: rgb(125,242,0);")
                    else:
                        
                        if settings.rec_color == settings.COLOR_RED:
                            cell.setStyleSheet("background-color: rgb(255, 102, 0);")
                        else:
                            cell.setStyleSheet("background-color: rgb(255, 21, 65);")        

    def onCurrentItemChanged(self, item):
        self.updatePreview(item)

    def loadScene(self, scene):
        try:
            self.gui.song.loadScene(scene)
            self.gui.updateScene(scene, self.scenelistList.currentRow()) 
            
        except:
            print("Error loading scene: " + str(scene))
            pass

    def useBigFonts(self, use = False):
        self.bigFontSize = settings.bigFontSize

        if use == False:
            stylesheet = 'font: 10pt "Noto Sans";'
        else:
            stylesheet = 'font: bold ' + str(self.bigFontSize) + 'pt "Noto Sans";'
         
        self.scenelistList.setStyleSheet(stylesheet)

    # Saving window position

    def resizeEvent(self, event):
        self.geometry = self.saveGeometry()
        settings.scenes_geometry = self.geometry

    def moveEvent(self, event):
        self.geometry = self.saveGeometry()
        settings.scenes_geometry = self.geometry

    def hideEvent(self, event):
        self.gui.actionScene_Manager.setEnabled(True)        

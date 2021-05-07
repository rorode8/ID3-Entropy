# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'test.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import numpy as np
import itertools
import math
import operator
import re

import os

global fila;
global columna;
global nivel;
global res;

class Node(object):
    def __init__(self,key, value):
        self.key = key
        self.value = value
        self.children = {}
    def add_child(self, node):
        self.children[node.key] = node
    def is_leaf(self):
        return self.children == {}
    def __str__(self):
        if(self.is_leaf()):
            return str(self.value)
        else:
           return  str(self.value)+'\n    '+ str(self.children)
    def __getitem__(self,key):
        return self.children[key]
    
    def hasChild(self,k):
        return k in self.children.keys()

def printTree(tree, indent=''):
    indent+='\t'
    s=indent+tree.value+'\n'
    
    
    if tree.is_leaf():
        return s
    else:
        indent+='\t'
        for k in tree.children.keys():
            s+=indent+k+'\n'
            #indent+='\t'
            s+=printTree(tree[k], indent)
        return s

def calculaEntropia(tabla, ycol):
    dftrain = tabla.copy();
    y_train = dftrain.pop(ycol)      #column to predict
    
    vocab = y_train.unique()
    
    entropy = {}
    for key, value in dftrain.iteritems():
        datos = dftrain[key].unique()
        cuenta = {}
        cuentaTups = {}
        tuplas = itertools.product(datos,vocab)
        for d in datos:
            cuenta[d]=0
        for t in tuplas:
            tup = tuple(t)
            cuentaTups[tup] = 0
        for index, row in dftrain.iterrows():
            cuenta[row[key]]+=1
            tup = tuple([row[key],str(y_train[index])])
            cuentaTups[tup]+=1
            
        n=sum(cuenta.values())
        ent = 0
        
        for k in cuenta:
            fir = cuenta[k]/n
            print("fir: "+str(cuenta[k])+'/'+str(n))
            sec=0
            for y in vocab:
                tup = tuple([k,y])
                print('tuple: '+str(tup))
                print(str(cuentaTups[tup])+'/'+str(cuenta[k]))
                
                if(cuentaTups[tup] == 0 or cuentaTups[tup] == cuenta[k]):
                    sec = 0
                else:
                    
                    sec += (cuentaTups[tup]/cuenta[k])*math.log2((cuentaTups[tup]/cuenta[k]))
            ent=ent +(fir *(-1)*(sec))
            print(ent)
        entropy[key]=ent
    return entropy

#Regresa la clave del valor más bajo del diccionario
def minKey(dicc):
    return min(dicc.items(), key=operator.itemgetter(1))[0];

#Trae al frente del dataframe la columna deseada
def frente(tabla, columna):
    primCol = tabla.pop(columna);
    tabla.insert(0, columna, primCol);

def obtenSubtablas(tabla, ycol):
    aux = minKey(calculaEntropia(tabla, ycol));
    frente(tabla, aux);
    tabla = tabla.sort_values(by=aux);
    subtablas= [];
    for i in tabla.iloc[:, 0].unique():
        subtablas.append(tabla.loc[(tabla.iloc[:, 0] == i)])
    return subtablas

def calculaReglas(tabla, ycol):
    subtablas = obtenSubtablas(tabla, ycol); 
    obtenReglas(subtablas, ycol, 0, 0);

def obtenReglas(subtablas, ycol, it, col): #Proceso iterativo general
    global columna
    global fila
    global nivel
    if it == 0:
        fila = 0;
        columna = 0;
        nivel = 0;
    for i in subtablas:
        subtabla = i.iloc[:,1:];
        aux = (i.columns[0] + " = " + i.iloc[0, 0]);
        if len(subtabla[ycol].unique()) > 1:
            res[fila][columna] = aux;
            columna = columna + 1;
            nivel = nivel + 1;
            obtenReglas(obtenSubtablas(subtabla, ycol), ycol, 1, col+1)
        else:
            res[fila][columna] = aux;
            res[fila][columna+1] = ycol + " = " + subtabla[ycol][:1].to_numpy()[0];
            fila = fila + 1;
            if nivel == 0:
                columna = col;
            else:
                nivel = nivel - 1;

def rellenaEspacios(matriz):
    sup = 0;
    for k in range(len(matriz[0])-1):
        for i in range(len(matriz)):
            if matriz[i][k] == '':
                matriz[i][k] = sup;
            sup = matriz[i][k];
            
def reglasInferencia(matriz, ycol):
    res = [];
    for i in range(len(matriz)):
        k = 0;
        ans = "if ";
        while k < len(matriz[0]) and ycol not in matriz[i][k]:
            ans= ans + "(" + matriz[i][k] + ") and ";
            k = k + 1;
        ans = ans[:len(ans)-4];
        ans = ans + "then (" + matriz[i][k] + ")"
        res.append(ans)
    return res

#Dada una matriz, una fila y una columna, regresa el primer elemento ubicado arriba de esa celda
def revisaSuperior(matriz, fila, columna):
    while fila > 0:
        if matriz[fila-1][columna] != '':
            return matriz[fila-1][columna].rpartition(" = ")[0]
        else:
            fila = fila - 1;
    return ''

def trasladaFilaIzq(matriz, fila):
    for i in range(len(matriz[0])-1):
        matriz[fila][i] = matriz[fila][i+1]

#Recibimos tabla que faltan deslazamientos de filas
def corrigeTabla(tabla): 
    for i in range(len(res)):
        bandera = True;
        j = len(res[0])-1
        while j in range(len(res[0])-1, 0, -1) and bandera:
            if tabla[i][j] != '' and tabla[i][j-1] == '':
                col = j-1;
                delta = 0;
                while col > 0 and delta == 0:
                    if revisaSuperior(tabla, i, col) in tabla[i][j]:
                        delta = j - col
                    else:
                        col = col - 1;
                for k in range(delta):
                    trasladaFilaIzq(tabla, i);
                bandera = False;
            else:
                j = j - 1;

def ultimaCorreccion(tabla):
    atributo = tabla[0][0].rpartition(" = ")[0];
    for i in range(len(tabla)):
        if atributo in tabla[i][1]:
            trasladaFilaIzq(tabla, i)

def genDic(reglas, ycol):
    
    stream = genline(reglas,ycol)
    
    labels = []
    d={}
    tree = None
    node = None
    i=0
    for r in stream:        
        print(r)
        print(type(r))
        k = {}
        for toks in r:
            
            print(toks)
            if(toks[0]==ycol):
                print('======')
                print(r)
                last = ""
                prev1, prev2 = "",""
                value=""
                node = tree
                for key, v in k.items():
                    value = str(key)+' '+str(v)
                    #print(str(key)+' '+str(value))
                    #print(tree.show())
                    if(tree==None):
                                                
                        tree=Node("root",key)                   
                        
                        
                        node = tree
                    else:
                        if(node.value != key):
                            
                            if(node.hasChild(prev2)):
                                node = node[prev2]
                            else:
                                node.add_child(Node(prev2,key))
                                node = node[prev2]
                        
                            
                        
                            
                    prev1, prev2 = key, v     
                    last = value
                    
                node.add_child(Node(prev2,toks[1]))
                #tree.create_node(toks[1], str(i),last)
                i+=1
                d[str(k)]=toks[1]
                
                print(str(tree))
                print(r)
                
            
            else:
                k[toks[0]]=toks[1]
                if(not toks[0] in labels):
                    labels.append(toks[0])
    return d, labels, tree
                    


def genline(reglas,ycol):
    
    stream = []
    for r in reglas:
        lista = []
        s = re.search('if\s(.*)\sthen',r)
        
        line = s.group(1)
        
        p = re.search('then\s\((.*)\)', r)
        prediction = p.group(1)
        
        rules=line.split(' and ')
        for rule in rules:
            l = rule[1:-1]
            toks = l.split(' = ')
            lista.append(toks)
            #print(toks)
        lista.append(prediction.split(' = '))
        stream.append(lista)
    return stream

class Ui_MainWindow(object):
    def __init__(self):
        self.df=None
        self.ycol=None
        self.ydf=None
        self.uniques = {}
        self.index = 0
        self.rules=None
        self.orderedEntropy = None
        self.predicted = False
        self.predictionCurrent = {}
        self.tree = None
        self.subtree = None


    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.groupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(30, 30, 731, 121))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.groupBox.setFont(font)
        self.groupBox.setObjectName("groupBox")
        self.openButton = QtWidgets.QPushButton(self.groupBox)
        self.openButton.setGeometry(QtCore.QRect(20, 50, 121, 31))
        self.openButton.setObjectName("openButton")
        self.lineEdit = QtWidgets.QLineEdit(self.groupBox)
        self.lineEdit.setGeometry(QtCore.QRect(170, 50, 491, 31))
        self.lineEdit.setObjectName("lineEdit")
        self.groupBox_2 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_2.setEnabled(True)
        self.groupBox_2.setGeometry(QtCore.QRect(30, 180, 731, 111))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.groupBox_2.setFont(font)
        self.groupBox_2.setObjectName("groupBox_2")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setGeometry(QtCore.QRect(150, 40, 71, 41))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.comboBox = QtWidgets.QComboBox(self.groupBox_2)
        self.comboBox.setGeometry(QtCore.QRect(260, 50, 191, 31))
        self.comboBox.setObjectName("comboBox")
        self.goButton = QtWidgets.QPushButton(self.groupBox_2)
        self.goButton.setGeometry(QtCore.QRect(540, 40, 111, 51))
        self.goButton.setObjectName("goButton")
        self.groupBox_3 = QtWidgets.QGroupBox(self.centralwidget)
        self.groupBox_3.setGeometry(QtCore.QRect(30, 320, 731, 201))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.groupBox_3.setFont(font)
        self.groupBox_3.setObjectName("groupBox_3")
        self.label_2 = QtWidgets.QLabel(self.groupBox_3)
        self.label_2.setGeometry(QtCore.QRect(60, 40, 51, 41))
        self.label_2.setObjectName("label_2")
        self.labelValue = QtWidgets.QLabel(self.groupBox_3)
        self.labelValue.setGeometry(QtCore.QRect(120, 50, 141, 21))
        self.labelValue.setObjectName("labelValue")
        self.label_3 = QtWidgets.QLabel(self.groupBox_3)
        self.label_3.setGeometry(QtCore.QRect(50, 80, 61, 31))
        self.label_3.setObjectName("label_3")
        self.comboVals = QtWidgets.QComboBox(self.groupBox_3)
        self.comboVals.setGeometry(QtCore.QRect(120, 80, 191, 31))
        self.comboVals.setObjectName("comboVals")
        self.predictButton = QtWidgets.QPushButton(self.groupBox_3)
        self.predictButton.setGeometry(QtCore.QRect(370, 60, 121, 51))
        self.predictButton.setObjectName("predictButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        #connect button
        self.openButton.clicked.connect(self.openFile)
        self.goButton.clicked.connect(self.goAction)
        self.predictButton.clicked.connect(self.predictAction)

        #enable
        self.groupBox_2.setEnabled(False)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox.setTitle(_translate("MainWindow", "File"))
        self.openButton.setText(_translate("MainWindow", "Open"))
        self.groupBox_2.setTitle(_translate("MainWindow", "Columns"))
        self.label.setText(_translate("MainWindow", "Y_col="))
        self.goButton.setText(_translate("MainWindow", "Go"))
        self.groupBox_3.setTitle(_translate("MainWindow", "Predict"))
        self.label_2.setText(_translate("MainWindow", "field:"))
        self.labelValue.setText(_translate("MainWindow", "value"))
        self.label_3.setText(_translate("MainWindow", "value:"))
        self.predictButton.setText(_translate("MainWindow", "Next"))

    def predictAction(self):

        if(self.predicted):
            self.subtree = self.tree

            self.labelValue.setText(self.subtree.value)
            self.comboVals.clear()
            self.comboVals.addItems(self.subtree.children.keys())

            self.predictButton.setText("Next")
            self.predicted = False
            return

        val = str(self.comboVals.currentText())

        self.subtree = self.subtree[val]    

        
        

        if(self.subtree.is_leaf()):

            result = self.subtree.value
            self.predicted = True
            
            self.predictButton.setText("Again")
            
            #show pop up
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("prediction")
            msg.setText(str(self.ycol)+" = "+str(result))
            x = msg.exec_()
            pass
        else:

            self.labelValue.setText(self.subtree.value)
            self.comboVals.clear()
            #self.comboVals.addItems(self.uniques[self.subtree.value])
            self.comboVals.addItems(self.subtree.children.keys())

            

    def goAction(self):
        self.ycol= str(self.comboBox.currentText())
        global res

        #calcula reglas
        tabla = self.df.copy()
        res = np.empty((len(tabla),len(tabla.columns)+1), dtype = "<U32");
        ycol = self.ycol
        calculaReglas(tabla, ycol)
        #Quitamos filas y columnas vacías
        res = res[~np.all(res == '', axis=1)]
        res = np.delete(res, np.argwhere(np.all(res[..., :] == '', axis=0)), axis=1)
        #Arreglamos desplazamientos defectuosos
        corrigeTabla(res)
        ultimaCorreccion(res)
        corrigeTabla(res)
        #Rellenamos espacios vacíos
        rellenaEspacios(res)  

        self.rules = reglasInferencia(res, ycol)
        arb , self.orderedEntropy, self.tree = genDic(self.rules,ycol)

        ##save to file overwrite rules
        f = open("rules.txt", "w")
        for line in self.rules:
            f.write(str(line)+'\n')
        f.close()

        arba = open("tree.txt", "w")
        
        arba.write(printTree(self.tree))

        arba.close()

        self.y_train = self.df.pop(self.ycol) 
        for key, value in self.df.iteritems():
            self.uniques[key] = list(self.df[key].unique())

        #copy tree
        self.subtree = self.tree

        self.index=0

        self.labelValue.setText(self.tree.value)
        self.comboVals.clear()
        self.comboVals.addItems(self.uniques[self.tree.value])

    def openFile(self):
        print('hi')
        #name = QtWidgets.QFileDialog.getOpenFileName(self,'Open File')
        #self.lineEdit.setText(name)
        name = self.open_dialog_box()[0]
        self.lineEdit.setText(name)
        self.groupBox_2.setEnabled(True)
        self.df = pd.read_csv(name)

        cols = list(self.df.columns)
        self.comboBox.clear()
        self.comboBox.addItems(cols)
        print(name)

    def open_dialog_box(self):
        filename = QtWidgets.QFileDialog.getOpenFileName()
        return filename



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

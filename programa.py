# -*- coding: utf-8 -*-
import sys

# Librerías de aceso a páginas web y datos
import requests                   # Realizar pedidos por medio de la www
import urllib.request             # hacer pedidos utilizando URL
import time
from bs4 import BeautifulSoup     # Manejar páginas web con hipertexto

# # #Importar aquí las librerías a utilizar # # #
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from firebase import firebase

# Librerías del PyQt
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSlot

from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)

# Nombre del archivo
qtCreatorFile = "ventana.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

# # # Funciones para ajuste de curvas # # #
# Función lineal
def lineal(x, a, b):
    return a*b + b
# Función exponencial
def exponencial(x, a, b):
    return a*np.exp(b*x)
# Función de ecuación de potencias 
def potencias(x, a, b):
    return a*np.power(x, b)
# Función gaussiana
def gaussiana(x, a, b, c):
    return a * np.exp(-np.power(x - b, 2)/(2*np.power(c, 2)))
# Función sigmoidal
def sigmoide(x, L ,x0, k, b):
    y = L / (1 + np.exp(-k*(x - x0))) + b
    return y

class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    # Constructor de la ventana
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        # Título de la ventana e ícono
        self.title = "Datos"
        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon('icono.ico'))
        
        # Colocar datos visibles o no visibles
        self.label_2.setVisible(False)
        self.label_3.setVisible(False)
        self.label_4.setVisible(False)
        self.label_5.setVisible(False)
        self.label_6.setVisible(False)
        self.plainTextEdit.setVisible(False)
        self.lineEdit_2.setVisible(False)
        self.lineEdit_3.setVisible(False)
        self.pushButton_2.setVisible(False)
        self.pushButton_3.setVisible(False)
        self.pushButton_4.setVisible(False)
        self.pushButton_5.setVisible(False)
        self.pushButton_6.setVisible(False)
        self.comboBox.setVisible(False)
        self.comboBox_2.setVisible(False)
        self.comboBox_3.setVisible(False)
        self.MplWidget.setVisible(False)
        
        # Controladores
        self.pushButton.clicked.connect(self.analizarURL)
        self.pushButton_2.clicked.connect(self.abrirURL)
        self.pushButton_3.clicked.connect(self.graficar)
        self.pushButton_4.clicked.connect(self.guardarLocal)
        self.pushButton_5.clicked.connect(self.guardarBD)
        self.pushButton_6.clicked.connect(self.ajustar)
        self.comboBox.currentTextChanged.connect(self.cambiarPais)
                        
        # Agregar la ToolBar para graficar
        #self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))
        
    # MÉTODOS DE LA CLASE
    def analizarURL(self):
        # Obtener la URL colocada
        url = self.lineEdit.text()
        # Obtener una respuesta
        respuesta = requests.get(url)
        # TODO: Eliminar esta línea que muestra datos en consola
        print(respuesta.status_code)
        # Revisar que el código de respuesta sea 200
        if respuesta.status_code == 200:
            # Crear la sopa de datos HTML
            sopa = BeautifulSoup(respuesta.text, "html.parser")
            # Ver todo el código
            self.plainTextEdit.setVisible(True)
            self.plainTextEdit.setPlainText(sopa.prettify())
            # Hallar las etiquetas que inicien con "a"
            # Obtener todos los posibles enlaces de archivos CSV
            self.listaEnlaces = []
            for enlace in sopa.findAll('a'):
                # Añadir el href para los enlaces a otras URL
                tmp = enlace.get('href')
                # Encontrar todos los posibles archivops CSV
                if(( "csv" in str(tmp) )):
                    # TODO: Eliminar el print a consola
                    print( str(tmp) )
                    self.listaEnlaces.append(tmp)
            # Analizar si se halló al menos un archivo CSV
            print(len(self.listaEnlaces))
            if len(self.listaEnlaces) > 0:
                self.label_2.setVisible(True)
                self.lineEdit_2.setVisible(True)
                self.pushButton_2.setVisible(True)
                self.lineEdit_2.setText(self.listaEnlaces[0][self.listaEnlaces[0].rfind('/')+1:])

    # Abrir la URL seleccionada
    def abrirURL(self):
        # Activar los widgets
        self.pushButton_3.setVisible(True)
        self.pushButton_4.setVisible(True)
        self.pushButton_5.setVisible(True)        
        self.label_3.setVisible(True)
        self.label_4.setVisible(True)
        self.label_5.setVisible(True)        
        self.comboBox.setVisible(True)
        self.comboBox_2.setVisible(True)        
        self.MplWidget.setVisible(True)
        
        # cargar los datos de manera temporal y directo de la URL con la librería pandas
        # UNDONE: Cambiar a archivo local para velocidad
        #self.df = pd.read_csv(self.listaEnlaces[0])
        self.df = pd.read_csv('owid-covid-data.csv')
        # Obtener los nombres de las columnas
        self.columnas = self.df.columns[4:]
        # Cargar los datos al combobox de países (de forma única en formato texto)
        self.comboBox.addItems(self.df["location"].unique().astype(str).tolist())
        # Junto con los datos de la tabla
        self.comboBox_2.addItems(self.columnas.unique().tolist())
        # Cargar los ajustes de curva posibles
        self.comboBox_3.addItems(["Lineal","Exponencial","Potencias","Gaussiana","Sigmoide"])
        
    # Cuando el nombre del país elegido cambie
    def cambiarPais(self):
        # Generar el posible nombre del archivo a guardar
        # Obtener la última fecha registrada
        ultimaFecha = self.df[self.df["location"] == self.comboBox.currentText()]["date"].tolist()[-1]
        print(ultimaFecha)
        
        nombre = self.comboBox.currentText() + str(ultimaFecha) + ".csv"
        # Colocar el nombre en el cuadro de texto
        self.lineEdit_3.setText(nombre)
        
    # Graficar los datos
    def graficar(self):
        # Activar el ajuste
        self.pushButton_6.setVisible(True)
        self.label_6.setVisible(True)
        self.lineEdit_3.setVisible(True)
        self.comboBox_3.setVisible(True)
        # Cargar los datos del combobox del país
        paisos = self.df[self.df["location"] == self.comboBox.currentText()]
        # Ahora revisar la columna con los datos a graficar
        datas = paisos[self.comboBox_2.currentText()].fillna(0).tolist()
        # Obtener las fechas
        fechas = paisos["date"].unique().tolist()
        # Pero se obtienen las fechas de cada 7 días para la gráfica
        fechas7 = fechas[::7]
        
        # Armar la gráfica
        # Limpiar la gráfica
        self.MplWidget.canvas.axes.clear()
        # Colocar los datos de la gráfica
        self.MplWidget.canvas.axes.plot(fechas, datas, color="blue", marker=".", linestyle="")
        # Colocar las etiquetas
        self.MplWidget.canvas.axes.set_ylabel(self.comboBox_2.currentText())
        self.MplWidget.canvas.axes.set_xlabel("Fecha")
        # TODO: Corregir el desplazamiento de las fechas
        # Rotar las fechas para una mejor vista
        self.MplWidget.canvas.axes.set_xticks(fechas7)
        self.MplWidget.canvas.axes.set_xticklabels(fechas7, rotation = 45)
        # Dibujar la gráfica
        self.MplWidget.canvas.draw()
        
        print(type(self.MplWidget.canvas.axes.get_position))
        
    # Guardar los dato del país en particular de forma local
    def guardarLocal(self):
        # obtener el nombre del TextEdit
        nombre = self.lineEdit_3.text()
        # Obtener los datos
        paisos = self.df[self.df["location"] == self.comboBox.currentText()]
        
        # Salvar en formato CSV        
        paisos.to_csv(str(nombre))
        
    # Guardar en una base de datos en la Nube (Firebase)
    def guardarBD(self):
        # Especificar el nombre de la base de datos
        # TODO: Colocar por fuera:
        bse = 'https://koreanovirooo.firebaseio.com/'
        # Abrir la conexión con la base de datos
        baseFuego = firebase.FirebaseApplication(bse,None)
        print(baseFuego)
        
        # Crear los datos a guardar
        paisos = self.df[self.df["location"] == self.comboBox.currentText()]
        # Armar los datos a enviar, con solamente los datos importantes
        # Rellenando los NaN con ceros, por cuestiones de la base de datos
        datosFinal = paisos[self.columnas.tolist()].fillna(0)
        print(datosFinal.head())
        
        # Convertir los datos a un diccionario con cada uno de los registros
        diccEnvio = datosFinal.to_dict('records')
        print(diccEnvio)
        
        # Generar la base de datos organizada
        pais = self.comboBox.currentText() + "/"
        print(pais)
        # Subir los registros uno por uno
        for k in range(len(diccEnvio)):
            result = baseFuego.put(pais, str(k), diccEnvio[k])
            print(result)
    
    def ajustar(self):
        # Obtener el nombre del ajuste
        tipoAjuste = self.comboBox_3.currentText().lower()
        
        # Mapear los nombres de las funciones
        funcionMap = {
                "lineal" : lineal,
                "exponencial" : exponencial,
                "potencias" : potencias,
                "gaussiana" : gaussiana,
                "sigmoide" : sigmoide,
                }

        # De las fechas hallar el total de datos para crear el arreglo en x
        x = np.arange(len(self.df[self.df["location"] == self.comboBox.currentText()]["date"].unique().tolist()))
        # Generar los datos para y
        y = np.array(self.df[self.df["location"] == self.comboBox.currentText()][self.comboBox_2.currentText()].fillna(0).tolist())
                
        # Parámetros del ajuste
        # TODO: Ajustar los parámetros a cada tipo
        if tipoAjuste == "sigmoide":
            p0 = [max(y), np.median(x), 1, min(y)]
        elif tipoAjuste == "gaussiana":
            p0 = [max(y),np.median(x), 10]
        else:
            p0 = [0,0]
        
        # TODO: Manejar las posibles excepciones
        # Realizar el ajuste
        pars, cov = curve_fit(f = funcionMap[tipoAjuste], xdata = x, ydata = y, p0 = p0, method='dogbox')
        
        # Graficar
        # Dibujar en la gráfica
        self.MplWidget.canvas.axes.plot(x, funcionMap[tipoAjuste](x, *pars), color="red")
        self.MplWidget.canvas.draw()
        


# FUNCIÓN MAIN
if __name__ == "__main__":
    app =  QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
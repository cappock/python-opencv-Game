# -*- coding: utf-8 -*-
"""
Created on Tue Oct 13 18:25:30 2020

@author: hector.guerra
"""
# Importaciones y librerias 
from pygame.locals import *
import pygame
import cv2
import sys
import numpy as np
import pygame_menu


#Metodo encargado de convertir una iamgen de Opencv a una imagen para pygame
def cvimage_to_pygame2(image):    
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(image.tostring(), image.shape[1::-1],
                                   "RGB")

#Modelos y clases para el juego
class Bolita(pygame.sprite.Sprite):
    #Inicializacion del objeto bolita
    def __init__(self, WIDTH, HEIGHT, velocidad):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('images/ball.png')
        self.image = pygame.transform.scale(self.image, (100,100))
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH/2 
        self.rect.centery = 50
        self.speed = [velocidad, -velocidad]
        self.colision = False 
    
    
    #Movimiento y colisiones con el entorno de la bolita
    def actualizar(self, time, cabeza, score):
        self.rect.centerx += self.speed[0] * time
        self.rect.centery += self.speed[1] * time
        
        
        #Choque con limites laterales
        if self.rect.left <= 0 or self.rect.right >= self.WIDTH:
            self.speed[0] = -self.speed[0]
            self.rect.centerx += self.speed[0] * time
            self.colision= False
        #Choque con limite superior
        if self.rect.top <= 0:
            self.speed[1] = -self.speed[1]
            self.rect.centery += self.speed[1] * time
            self.colision= False
        #Choque con limite inferior, es un trigger para el fin del juego
        if self.rect.bottom >= self.HEIGHT:
            score[1] += 1
            self.colision = False
        #Deteccion de colision con la cabeza del jugador
        if pygame.sprite.collide_rect(self, cabeza) and self.colision == False:
            score[0] += 1 
            self.colision= True
            if self.rect.centerx <= cabeza.rect[0]:    
                self.speed[0] = -self.speed[0]
            elif self.rect.centery <= cabeza.rect[1]:
                self.speed[1] = -self.speed[1]
            elif self.rect.centerx <= cabeza.rect[0] + cabeza.rect[2]:
                self.speed[0] = -self.speed[0]
            elif self.rect.centery <= cabeza.rect[1] + cabeza.rect[3]:
                self.speed[1] = -self.speed[1]    
            
            self.rect.centerx += self.speed[0] * time
            self.rect.centery += self.speed[1] * time

#Objeto que nos permite coveertir un area o rectagulo en sprite de pygame y podeer deetectar colisiones
class Cabeza(pygame.sprite.Sprite):
    def __init__(self, posicion, Wight, Hight):
        pygame.sprite.Sprite.__init__(self)
        self.radio = Wight
        self.rect = (posicion[0], posicion[1] , Wight, Hight )

#Metodo para mostrar un texto en pantalla
def texto(texto, posx, posy, color=(255,255,255)):
    fuente = pygame.font.SysFont("comicsansms", 65)
    salida = pygame.font.Font.render(fuente, texto, 1, color)
    salida_rect = salida.get_rect()
    salida_rect.centerx = posx
    salida_rect.centery = posy
    return salida, salida_rect


#Metodo para la creacion de botones
def Buttonify(Picture, coords):
    image = pygame.image.load(Picture)
    imagerect = image.get_rect()
    imagerect.topright = coords
    return (image,imagerect)

#Importar modelo entrenado para la deteccion de rostros
faceClassif = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

def detectarRostro(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceClassif.detectMultiScale(gray, 1.3, 5)
    rostro = None 
    for (x,y,w,h) in faces:
        rostro = Cabeza((x ,y), w, h )
        
    return frame, rostro 

def actualizarPantalla(bola,cabeza, clock, score, frameCv, screen, botonVolverAJugar, botonQuit):
    global WIDTH
    time = clock.tick(30)
    botonActivo = False
    
    screen.blit(cvimage_to_pygame2(frameCv), (0, 0))
    bola.actualizar(time,cabeza,score)
    scoreImage = pygame.image.load('images/score.png')
    screen.blit(scoreImage,(320,0))
    
    p_jug, p_jug_rect = texto(str(score[0]),400, 45)
    screen.blit(p_jug, p_jug_rect)
    screen.blit(bola.image, bola.rect) 
    
    
    #Control para el final del juego
    if(score[1] >= 1):         
        JuegoTerminado = pygame.image.load('images/gameOver.png')
        screen.blit(JuegoTerminado,(0,115))
        screen.blit(botonQuit[0],botonQuit[1])
        screen.blit(botonVolverAJugar[0],botonVolverAJugar[1])
        botonActivo = True
        
    cv2.imshow('frame',frameCv)     
    pygame.display.update()
    
    return botonActivo


def start(camera):
    
    WIDTH = 480
    HEIGHT = 640

    velocidad = 0.2
    score = [0,0]
    screen = pygame.display.set_mode([480,640])

    botonVolverAJugar = Buttonify('images/tryAgain.png', (350,415))
    botonQuit = Buttonify('images/exit.png', (350,515))
    botonActivo = False
    
    clock = pygame.time.Clock()
    

    try:
        
        cabeza = Cabeza((50,50), 50, 50)
        bola = Bolita(WIDTH, HEIGHT,velocidad)

        while True:

            ret, frame = camera.read()    
            screen.fill([0, 0, 0])

            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.flip(frame, 1) 

            frame, rostro = detectarRostro(frame)
            cabeza = cabeza if rostro is None else rostro  

            botonActivo = actualizarPantalla(bola, cabeza, clock, score, frame, screen, botonVolverAJugar, botonQuit)

            for event in pygame.event.get():
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    mouse = event.pos
                    if botonVolverAJugar[1].colliderect([mouse[0], mouse[1], 1, 1]) and botonActivo==True:
                        start(camera)
                    if botonQuit[1].colliderect([mouse[0], mouse[1], 1, 1]) and botonActivo==True:
                        pygame.quit()
                        camera.release()
                        sys.exit(0)
                        
                if event.type == pygame.QUIT:
                    pygame.quit()
                    camera.release()
                    sys.exit(0)                    
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE or event.key == K_q:
                        pygame.quit()
                        camera.release()
                        sys.exit(0)
                        

    except (KeyboardInterrupt, SystemExit):
        pygame.quit()
        camera.release()
        pygame_menu.events.EXIT
        cv2.destroyAllWindows()
        





def start_the_game():
    start(camera)
    pass

##Inicio del Sistema 
pygame.init()
surface = pygame.display.set_mode((480, 640))
camara = 'http://192.168.1.51:4747/video'
camera = cv2.VideoCapture(camara)

try:
    menu = pygame_menu.Menu(300, 400, 'Cabecea La Pelota',
                           theme=pygame_menu.themes.THEME_BLUE)

    menu.add_button('Jugar', start_the_game)
    menu.add_button('Salir', pygame_menu.events.EXIT)

    menu.mainloop(surface)
except:
    pygame.quit()
    camera.release()
    cv2.destroyAllWindows()



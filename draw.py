#!/usr/bin/env python3

"""
génération d'une image animée représentant la simulation de Monte-Carlo
"""

import glob
import sys
import subprocess
import os
from collections import namedtuple
from approximate_pi import points_generator, Point

def point_to_pixel(point, image_size):
    """
    convertit le point de coordonnée x,y avec x et y dans [-1,1]
    à un pixel appartenant à l'image de taille image_size
    """
    pixel_x = int((image_size/2)*(point.x + 1))
    pixel_y = int((image_size/2)*(-point.y + 1))
    return (pixel_x, pixel_y)

def modify_pixels(tab, nb_points, generate_points):
    """
    Modifications de la table de pixels pour chaque point fourni par le module approximate_pi.
    Les points à l'intérieur du cercle unitaire sont mis en rouge et
    ceux à l'extérieur en vert. La fonction renvoie ensuite la valeur courante de pi.
    """
    size = len(tab)
    for _ in range(0, nb_points//10):
        point, point_in_circle = next(generate_points)
        pixel_x, pixel_y = point_to_pixel(point, size)
        if point_in_circle:
            tab[pixel_x][pixel_y] = (1, 0, 0)
        else:
            tab[pixel_x][pixel_y] = (0, 1, 0)
    # Remarque: Avec cette méthode, si plusieurs points tirés tombent sur le même pixel,
    # ce pixel prendra alors la couleur correspondant au dernier point tiré
    current_pi = next(generate_points)
    return current_pi

def seven_segments_in_ppm(number, size, writing_length, distance_to_edge):
    """
    retourne un set des pixels à mettre en noirs pour écrire le nombre donné en argument
    par la méthode des sept segments
    """
    # Définition de la structure case composée de trois attributs: le point situé en haut à gauche,
    # la hauteur et la largeur
    Case = namedtuple('Case', 'depart largeur hauteur')

    # On définit les fonctions nécessaires pour tracer les différents segments
    # Pour chaque segment, et pour la case et l'épaisseur d'écriture donnée, la fonction
    # retourne un set des pixels à mettre en noir pour tracer le segment
    def top_segment(case, writing_thickness):
        """Tracé du segment en haut"""
        black_pixels = set()
        for k in range(writing_thickness):
            for i in range(0, case.largeur):
                black_pixels.add((case.depart.y+k, case.depart.x+i))
        return black_pixels

    def top_left_segment(case, writing_thickness):
        """Tracé du segment en haut à gauche"""
        black_pixels = set()
        for k in range(writing_thickness):
            for i in range(0, (case.hauteur)//2):
                black_pixels.add((case.depart.y+i, case.depart.x+k))
        return black_pixels

    def top_right_segment(case, writing_thickness):
        """Tracé du segment en haut à droite"""
        black_pixels = set()
        for k in range(writing_thickness):
            for i in range(0, (case.hauteur)//2):
                black_pixels.add((case.depart.y+i, case.depart.x+case.largeur-k))
        return black_pixels

    def middle_segment(case, writing_thickness):
        """Tracé du segment du milieu"""
        black_pixels = set()
        for k in range(writing_thickness):
            for i in range(0, case.largeur):
                black_pixels.add((case.depart.y+case.hauteur//2+k, case.depart.x+i))
        return black_pixels

    def bottom_left_segment(case, writing_thickness):
        """Tracé du segment en bas à gauche"""
        black_pixels = set()
        depart = case.depart.y + case.hauteur//2
        for k in range(writing_thickness):
            for i in range(0, (case.hauteur)//2):
                black_pixels.add((depart+i, case.depart.x+k))
        return black_pixels

    def bottom_right_segment(case, writing_thickness):
        """Tracé du segment en bas à droite"""
        black_pixels = set()
        depart = case.depart.y + case.hauteur//2
        for k in range(writing_thickness):
            for i in range(0, (case.hauteur)//2):
                black_pixels.add((depart+i, case.depart.x+case.largeur-k))
        return black_pixels

    def bottom_segment(case, writing_thickness):
        """Tracé du segment en bas"""
        black_pixels = set()
        for k in range(writing_thickness):
            for i in range(0, case.largeur):
                black_pixels.add((case.depart.y+case.hauteur-k, case.depart.x+i))
        return black_pixels

    def point_segment(case, writing_thickness):
        """Tracé d'un point"""
        black_pixels = set()
        for k in range(writing_thickness):
            for i in range(0, 3):
                for j in range(0, 3):
                    black_pixels.add((case.depart.y+case.hauteur-j-k, case.depart.x+i+k))
        return black_pixels

    # On définit un dictionnaire de chiffres: pour chaque chiffre, on indique les segments
    # nécessaires pour son tracé
    segments = {
        '0':(top_segment, top_left_segment, top_right_segment,\
            bottom_left_segment, bottom_right_segment, bottom_segment),
        '1':(top_right_segment, bottom_right_segment),
        '2':(top_segment, top_right_segment, middle_segment, bottom_left_segment,\
            bottom_segment),
        '3':(top_segment, top_right_segment, middle_segment, bottom_right_segment, bottom_segment),
        '4':(top_left_segment, top_right_segment, middle_segment, bottom_right_segment),
        '5':(top_segment, top_left_segment, middle_segment, bottom_right_segment, bottom_segment),
        '6':(top_segment, top_left_segment, middle_segment, bottom_left_segment,\
            bottom_right_segment, bottom_segment),
        '7':(top_segment, top_right_segment, bottom_right_segment),
        '8':(top_segment, top_left_segment, top_right_segment, middle_segment,\
            bottom_left_segment, bottom_right_segment, bottom_segment),
        '9':(top_segment, top_left_segment, top_right_segment, middle_segment,\
            bottom_right_segment, bottom_segment),
        '.':[point_segment]
    }

    # Définition de différentes constantes nécessaires pour l'écriture.
    # Toutes ces constantes doivent varier en fonction de la taille de l'image
    writing_thickness = size//500 + 1
    digits_spacing = size//100
    digit_width = (writing_length - digits_spacing*(len(number)-1))//len(number)

    pixels_in_black = set()

    for i, chiffre in enumerate(number):
        # On découpe la zone d'écriture en cases, à chaque chiffre correspond une case d'écriture
        starting_abscissa = distance_to_edge + (digit_width + digits_spacing)*i
        top_left_point = Point(starting_abscissa, distance_to_edge)
        case = Case(top_left_point, digit_width, size - distance_to_edge*2)
        for fonction in segments[chiffre]:
            pixels_in_black.update(fonction(case, writing_thickness))
    return pixels_in_black

def generate_ppm_file(tab, img_name, current_pi):
    """
    génère l'image numéro numimage de la simulation
    """
    size = len(tab)
    img = open(f"{img_name}", "wb")
    entete = f"P6\n{size} {size}\n1\n"
    img.write(bytes(entete, 'UTF-8'))

    # Définition des constantes permettant de déterminer la zone de l'image sur laquelle
    # on écrit la valeur de pi
    writing_length = size//5
    distance_to_edge = int(size/2.25)

    black_pixels = seven_segments_in_ppm(current_pi, size, writing_length, distance_to_edge)

    for i in range(size):
        for j in range(size):
            red, green, blue = tab[i][j]
            # On vérifie si le pixel est dans la zone d'écriture de la valeur de pi
            if distance_to_edge <= i <= size - distance_to_edge and \
                distance_to_edge <= j <= distance_to_edge + writing_length:
                if (i, j) in black_pixels:
                    red, green, blue = 0, 0, 0
                    img.write(bytes('%c%c%c' % (red, green, blue), 'UTF-8'))
                    black_pixels.remove((i, j))
                else:
                    img.write(bytes('%c%c%c' % (red, green, blue), 'UTF-8'))
            else:
                img.write(bytes('%c%c%c' % (red, green, blue), 'UTF-8'))
    img.close()

def main():
    """
    géneration d'une image représentant la simulation de Monte-Carlo
    """
    if len(sys.argv) != 4 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("utilisation:", sys.argv[0],\
            "[taille de l'image] [nombre de points] [nombre de chiffres après la virgule]")
        sys.exit(1)
    else:
        image_size = int(sys.argv[1])
        nb_points = int(sys.argv[2])
        nb_decimals = int(sys.argv[3])
        # L'utilisation de la fonction int permet de vérifier par la même occasion
        #  que les arguments fournis sont bien des entiers

        # On vérifie si les arguments donnés sont dans le bon intervalle
        if image_size < 100:
            raise ValueError("La taille de l'image doit être un entier supérieur ou égal à 100")
        if nb_points < 100:
            raise ValueError("Le nombre de points n à utiliser dans la simulation \
                doit être supérieur ou égal à 100")
        if not 1 <= nb_decimals <= 5:
            raise ValueError("Le nombre de chiffres après la virgule doit être \
                compris entre 1 et 5")

        # Définition et initialisation de la table des pixels
        tab = []
        for _ in range(image_size):
            tab.append([(1, 1, 1)]*image_size)

        generate_points = points_generator(nb_points)

        for numimage in range(0, 10):
            current_pi = modify_pixels(tab, nb_points, generate_points)
            current_pi = f"{current_pi:.{nb_decimals}f}"
            pi_units = current_pi[0]
            pi_decimals = current_pi[2:len(current_pi)]
            img_name = f"img{numimage}_{pi_units}-{pi_decimals}.ppm"
            generate_ppm_file(tab, img_name, current_pi)

        try:
            # On utilise glob pour lister tous les fichiers .ppm
            image_files = sorted(glob.glob("img*.ppm"))
            if not image_files:
                raise FileNotFoundError("Pas de fichiers .ppm sous la forme 'img*.ppm'.")

            # On crée l'image gif en utilisant la commande 'convert' de ImageMagick
            command = ['convert', '-delay', '100'] + image_files + ['image.gif']
            subprocess.run(command, check=True)
            print("GIF 'image.gif' créé avec succès.")

            # On supprime les fichiers .ppm utilisés
            for file in image_files:
                os.remove(file)
            print("Fichiers .ppm temporaires supprimés.")
        except Exception as e:
            print(f"Une erreur est survenue: {e}")

if __name__ == "__main__":
    main()

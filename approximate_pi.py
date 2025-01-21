#!/usr/bin/env python3

"""Approximation de la valeur de pi par la simulation de Monte-Carlo"""

from collections import namedtuple
import sys
from random import uniform

# Definition de la structure Point composée de deux attributs x et y
Point = namedtuple('Point', 'x y')

def is_in_circle(point):
    """
    renvoie True si le point est dans le cercle et False sinon
    """
    return (point.x)**2 + (point.y)**2 <= 1

def random_point():
    """
    renvoie un point tiré alétoirement dans [-1,1]² et un booléen indiquant
    si le point est ou n'est pas dans le cercle unité
    """
    abscissa = uniform(-1, 1)
    ordinate = uniform(-1, 1)
    point = Point(abscissa, ordinate)
    point_in_circle = is_in_circle(point)
    return point, point_in_circle

def points_generator(nb_points):
    """
    génerateur des nbpoints à utiliser dans la simulation. A chaque fois qu'1/10
    des points ont été tirés, le générateur donne la valeur courante de pi
    """
    nbpoints_in = 0
    for i in range(10):
        for _ in range(nb_points//10):
            point, point_in_circle = random_point()
            if point_in_circle:
                nbpoints_in += 1
            yield point, point_in_circle
        yield (nbpoints_in/(nb_points*(i+1)//10))*4

def estimation_pi(nbpoints):
    """
    retourne une estimation de la valeur de pi si on tire aléatoirement nbpoints
    """
    nbpoints_in = 0
    for _ in range(nbpoints):
        if random_point()[1]:
            nbpoints_in += 1
    return (nbpoints_in/nbpoints)*4

def main():
    """
    approximation de la valeur de pi
    """
    if len(sys.argv) != 2 or sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("utilisation:", sys.argv[0], "[nombre de tirages aléatoires]")
    else:
        nbpoints = int(sys.argv[1])
        print(estimation_pi(nbpoints))

if __name__ == "__main__":
    main()

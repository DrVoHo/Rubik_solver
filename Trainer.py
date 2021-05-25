#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

# Quelle für Schema: http://mordred.awardspace.us/OLLCheatSheet.pdf
 
import os
 
Training_pattern = []

Trainingliste = 0
 
HOME = "/home/pi/"
 
def init():
	global Training_pattern
	global Trainingliste
	dummy = []
	if os.path.exists(HOME + "Speedcubing.txt"):
		f=open(HOME + "Speedcubing.txt", 'r')
		for line in f:
			line = line[:len(line)-1]   #remove cr
			dummy.append(line)
		for i in range(0, len(dummy),2):
			Training_pattern.append(dummy[i])
			print(dummy[i])
			text = reverse_string(dummy[i+1])
			Training_pattern.append(text)
			print(text)
		Trainingliste = len(Training_pattern)/2

def reverse_string(pattern):
	print ("org " + pattern)
	pattern = pattern.replace("(","")
	pattern = pattern.replace(")","")
	
	pattern = pattern.replace("R2'","R2")
	pattern = pattern.replace("L2'","L2")
	pattern = pattern.replace("U2'","U2")
	pattern = pattern.replace("D2'","D2")
	pattern = pattern.replace("F2'","F2")
	pattern = pattern.replace("B2'","B2")

	pattern = pattern.replace("M2","r2 R2")
	pattern = pattern.replace("E2","u2 U2")
	pattern = pattern.replace("S2","f2 F2")

	pattern = pattern.replace("l2'","l' l'")
	pattern = pattern.replace("r2'","r' r'")
	pattern = pattern.replace("f2'","f' f'")
	pattern = pattern.replace("b2'","b' b'")
	pattern = pattern.replace("u2'","u' u'")
	pattern = pattern.replace("d2'","d' d'")
	
	pattern = pattern.replace("x2'","x' x'")
	pattern = pattern.replace("y2'","y' y'")
	pattern = pattern.replace("z2'","z' z'")
	pattern = pattern.replace("x2","x x")
	pattern = pattern.replace("y2","y y")
	pattern = pattern.replace("z2","z z")

	pattern = pattern.replace("l2","l l")
	pattern = pattern.replace("r2","r r")
	pattern = pattern.replace("f2","f f")
	pattern = pattern.replace("b2","b b")
	pattern = pattern.replace("u2","u u")
	pattern = pattern.replace("d2","d d")
	
	pattern = pattern.replace("M'","Q")
	pattern = pattern.replace("M","r' R")
	pattern = pattern.replace("Q","r R'")
	
	pattern = pattern.replace("E'","Q")
	pattern = pattern.replace("E","u' U")
	pattern = pattern.replace("Q","u U'")
	
	pattern = pattern.replace("S'","Q")
	pattern = pattern.replace("S","f F'")
	pattern = pattern.replace("Q","f' F")
	
	pattern = pattern.replace("l'","Q")   # l ->  R x'
	pattern = pattern.replace("l","R x'")
	pattern = pattern.replace("Q","R' x")
	
	pattern = pattern.replace("r'","Q")   #r ->  L x  
	pattern = pattern.replace("r","L x")
	pattern = pattern.replace("Q","L' x'")
	
	pattern = pattern.replace("f'","Q")  #f -> B z
	pattern = pattern.replace("f","B z")
	pattern = pattern.replace("Q","B' z'")
	
	pattern = pattern.replace("b'","Q")   #b ->  F z'
	pattern = pattern.replace("b","F z'")
	pattern = pattern.replace("Q","F' z")
	
	pattern = pattern.replace("u'","Q")   #u -> D y
	pattern = pattern.replace("u","D y")
	pattern = pattern.replace("Q","D' y'")
	
	pattern = pattern.replace("d'","Q")    #d -> U y'
	pattern = pattern.replace("d","U y'")
	pattern = pattern.replace("Q","U' y")
	

	
	print("first replace " + pattern)
	
	reverse_string =""
	dummy_array = []
	dummy_array = pattern.split(" ")
#	print(dummy_array)
	for i in range(0,len(dummy_array)):
		reverse_string=reverse_string + " " + dummy_array[len(dummy_array)-1-i]
#	for i in dummy_array:
#		reverse_string=reverse_string+ " " + dummy_array[len(dummy_array) - 1 - dummy_array.index(i)]
	print ("order changed" + reverse_string)
	reverse_string=change(reverse_string,"L")   # Drehrichtungen umkehren
	reverse_string=change(reverse_string,"R")
	reverse_string=change(reverse_string,"U")
	reverse_string=change(reverse_string,"D")
	reverse_string=change(reverse_string,"F")
	reverse_string=change(reverse_string,"B")
	reverse_string=change(reverse_string,"x")
	reverse_string=change(reverse_string,"y")
	reverse_string=change(reverse_string,"z")
	
	print ("direction changed" + reverse_string)
	
	dummy_string=""
	part = reverse_string.split(" ",1)
	
	while len(part)>=1:
		if part[0]=="x" and len(part)==2:
			part[1]=change_x(part[1])
		elif part[0]=="x'" and len(part)==2:
			part[1]=change_x2(part[1])
		elif part[0]=="y" and len(part)==2:
			part[1]=change_y(part[1])
		elif part[0]=="y'" and len(part)==2:
			part[1]=change_y2(part[1])
		elif part[0]=="z" and len(part)==2:
			part[1]=change_z(part[1])
		elif part[0]=="z'" and len(part)==2:
			part[1]=change_z2(part[1])
		else:
			dummy_string = dummy_string + " " + part[0]
		if len(part)==2:
			part =part[1].split(" ",1)
		else:
			part = []
		
	print("removed cube turns  " + dummy_string)
	
	dummy_string = dummy_string.replace("R R","R2")
	dummy_string = dummy_string.replace("R' R'","R2")
	dummy_string = dummy_string.replace("F F","F2")
	dummy_string = dummy_string.replace("F' F'","F2")
	dummy_string = dummy_string.replace("L L","L2")
	dummy_string = dummy_string.replace("L' L'","L2")
	dummy_string = dummy_string.replace("B B","B2")
	dummy_string = dummy_string.replace("B' B'","B2")
	dummy_string = dummy_string.replace("U U","U2")
	dummy_string = dummy_string.replace("U' U'","U2")
	dummy_string = dummy_string.replace("D D","D2")
	dummy_string = dummy_string.replace("D' D'","D2")
	
	return dummy_string
			
		
	


def change(string, char):	
	string = string.replace(char + "2","Q1")
	string = string.replace(char + "'","Q2")
	string = string.replace(char, char +"'")
	string = string.replace("Q1",char + "2")
	string = string.replace("Q2",char)
	return string

	# xyz entfernen
	# x:  F<-U U<-B B<-D D<-F z<-y z'<-y' y<-z' y'<-z
    # x:  
def change_x(part):	
	part=part.replace("F","Q")
	part=part.replace("U","F")
	part=part.replace("B","U")
	part=part.replace("D","B")
	part=part.replace("Q","D")
	part=part.replace("z'","Q1")
	part=part.replace("y'","Q2")
	part=part.replace("z","Q3")
	part=part.replace("y","Q4")
	part=part.replace("Q1","y")
	part=part.replace("Q2","z'")
	part=part.replace("Q3","y'")
	part=part.replace("Q4","z")
	return part

	# x': F<-D U<-F B<-U D<-B y<-z y'<-z' z<-y' z'<-y
def change_x2(part):
	part=part.replace("F","Q")
	part=part.replace("D","F")
	part=part.replace("B","D")
	part=part.replace("U","B")
	part=part.replace("Q","U")
	part=part.replace("z'","Q1")
	part=part.replace("y'","Q2")
	part=part.replace("z","Q3")
	part=part.replace("y","Q4")
	part=part.replace("Q1","y'")
	part=part.replace("Q2","z")
	part=part.replace("Q3","y")
	part=part.replace("Q4","z'")
	return part

	# y:  R<-F F<-L L<-B B<-R x<-z x'<-z' z<-x' z'<->x
def change_y(part):
	part=part.replace("F","Q")
	part=part.replace("L","F")
	part=part.replace("B","L")
	part=part.replace("R","B")
	part=part.replace("Q","R")
	part=part.replace("x'","Q1")
	part=part.replace("z'","Q2")
	part=part.replace("x","Q3")
	part=part.replace("z","Q4")
	part=part.replace("Q1","z")
	part=part.replace("Q2","x'")
	part=part.replace("Q3","z'")
	part=part.replace("Q4","x")
	return part

	# y': R<-B B<-L L<-F F<-R x<-z' x'<-z z<-x z'<-x'	
def change_y2(part):
	part=part.replace("F","Q")
	part=part.replace("R","F")
	part=part.replace("B","R")
	part=part.replace("L","B")
	part=part.replace("Q","L")
	part=part.replace("x'","Q1") 
	part=part.replace("z'","Q2")
	part=part.replace("x","Q3")
	part=part.replace("z","Q4")
	part=part.replace("Q1","z'")
	part=part.replace("Q2","x")
	part=part.replace("Q3","z")
	part=part.replace("Q4","x'")
	return part
	
	# z:  U<-R R<-D D<-L L<-U y<-x y'<-x' x<-y' x'<-y
def change_z(part):
	part=part.replace("U","Q")
	part=part.replace("R","U")
	part=part.replace("D","R")
	part=part.replace("L","D")
	part=part.replace("Q","L")
	part=part.replace("x'","Q1") 
	part=part.replace("y'","Q2")
	part=part.replace("x","Q3")
	part=part.replace("y","Q4")
	part=part.replace("Q1","y'")
	part=part.replace("Q2","x")
	part=part.replace("Q3","y")
	part=part.replace("Q4","x'")
	return part
	# z': R<-U U<-L L<-D D<-R x<-y x'<-y' y<-x' y'<-x	
def change_z2(part):
	part=part.replace("U","Q")
	part=part.replace("L","U")
	part=part.replace("D","L")
	part=part.replace("R","D")
	part=part.replace("Q","R")
	part=part.replace("x'","Q1") 
	part=part.replace("y'","Q2")
	part=part.replace("x","Q3")
	part=part.replace("y","Q4")
	part=part.replace("Q1","y")
	part=part.replace("Q2","x'")
	part=part.replace("Q3","y'")
	part=part.replace("Q4","x")
	return part
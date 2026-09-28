import sys
import math
import string
import random

import pygame


def run(window_size=(1400, 1200)):
	pygame.init()
	screen = pygame.display.set_mode(window_size)
	pygame.display.set_caption("Alphabet Keyboard")

	w, h = window_size
	cx, cy = w // 2, h // 2
	# size and layout for keyboard keys at bottom
	square_size = 96
	letters = list(string.ascii_uppercase)
	n = len(letters)

	# keyboard rows (QWERTY layout for letters only)
	kb_rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
	row_spacing = int(square_size * 0.4)
	bottom_margin = 40

	# compute positions for each letter keyed to the alphabet index order
	letter_positions = [None] * n
	# vertical positions for rows (from bottom, positioned so bottom row is visible)
	total_keyboard_height = len(kb_rows) * square_size + (len(kb_rows) - 1) * row_spacing
	start_y = h - bottom_margin - total_keyboard_height
	for r, row in enumerate(kb_rows):
		row_len = len(row)
		spacing = int(square_size * 0.15)
		row_width = row_len * square_size + (row_len - 1) * spacing
		start_x = (w - row_width) // 2
		y = start_y + r * (square_size + row_spacing)
		for i, ch in enumerate(row):
			x = start_x + i * (square_size + spacing) + square_size // 2

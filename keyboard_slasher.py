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
			idx = letters.index(ch)
			letter_positions[idx] = pygame.math.Vector2(int(x), int(y))

	# how close the selector must be to a letter to count as 'at' that letter
	space_tolerance = max(12, int(square_size * 0.3))

	clock = pygame.time.Clock()
	font = pygame.font.SysFont(None, int(square_size * 0.6))
	word_font = pygame.font.SysFont(None, 48)

	# word lists by difficulty
	easy_words = ["apple", "banana", "cherry", "dragon", "eagle", "forest", "golden", "human", "island", "jungle",
	              "kitchen", "lemon", "mountain", "numbers", "orange", "purple", "quality", "rainbow", "silver", "tiger",
	              "umbrella", "violin", "watered", "xylophone", "yellow", "zone", "animal", "bright", "clean", "dream",
	              "enjoy", "friend", "gentle", "happy", "inside", "journey", "knight", "letter", "magic", "nature",
	              "outside", "people", "question", "reason", "simple", "teacher", "unique", "village", "window", "zebra",
	              "keyboard", "typing", "python", "gaming", "music", "coding", "racing", "shader", "render", "pixel"]
	
	medium_words = ["algorithm", "bandwagon", "calendar", "dangerous", "excellent", "furniture", "guarantee", "hurricane", "initiative", "jealousy",
	                "language", "mysterious", "necessary", "operation", "parameter", "rectangle", "separate", "territory", "electricity",
	                "financial", "generation", "horizontal", "important", "judgment", "liberal", "mathematics", "newspaper", "official", "particular",
	                "restaurant", "signature", "television", "vacation", "wonderful", "youngster", "zeppelin", "acceptable", "background", "calculation",
	                "digital", "method", "function", "variable", "string", "number", "boolean", "object", "array", "class",
	                "interface", "abstract", "public", "private", "static", "final", "super", "this", "else", "switch",
	                "while", "return", "import", "export", "module", "library", "framework", "package", "compile", "runtime"]
	
	hard_words = ["abjure", "abscond", "buzzword", "beguile", "bureaucracy", "cacophony", "callous", "capacity", "carcinogenic",
	              "carpentry", "catastrophe", "category", "catharsis", "caucasian", "crystallize", "connoisseur", "conscience", "conscientious", "consequence",
	              "bureaucratic", "complacency", "concatenate", "cryptocurrency", "cyclical", "deleterious", "dexterity", "dichotomy", "diligence", "disquiet",
	              "dystopian", "eccentricity", "ecclesiastical", "effervescent", "egregious", "encyclopedia", "ephemeral", "equanimity", "esoteric", "ethnography",
	              "etymology", "euphemism", "felicity", "fervently", "fiduciary", "fluorescent", "frivolous", "functionality", "fundamental", "generosity",
	              "pseudocholinesterase", "supercalifragilisticexpialidocious", "antidisestablishmentarianism", "incomprehensibility", "dichlorodifluoromethane",
	              "uncharacteristically", "telecommunications", "disproportionately", "counterrevolutionary", "internationalization",
	              "subconsciously", "extraterrestrial", "unquestionably", "responsibilities", "characteristics",
	              "acknowledgements", "accomplishments", "administration", "catastrophically", "chronological"]
	
	# select one word from each difficulty
	current_words = [random.choice(easy_words), random.choice(medium_words), random.choice(hard_words)]
	word_difficulties = ["easy", "medium", "hard"]
	word_progress = [0, 0, 0]  # current letter index for each word

	# selector state: position and target 
	selector_pos = pygame.math.Vector2(cx, cy)
	target_pos = None
	# movement/slash timing 
	slash_dur = 0.22 / 3.0
	# selector movement will be time-based and matched to slash_dur
	selector_move_t = 0.0
	selector_move_dur = 0.0
	selector_start_pos = selector_pos.copy()
	selector_speed = 36 * 60
	# active slash effects
	slashes = []
	# word completion mode: completing a word makes the NEXT slash light-blue and duplicated
	pending_double = False
	# selector colors
	green_color = (144, 238, 144)
	blue_color = (173, 216, 230)
	red_color = (255, 90, 90)
	selector_color = green_color
	# track active blue slashes so we can restore color when done
	blue_count = 0
	selected_index = None
	# queue for buffered key inputs when selector is moving (max 3)
	input_queue = []

	# BUGFIX: miss flash state - shown briefly when a wrong letter is pressed
	miss_flash_t = 0.0
	MISS_FLASH_DUR = 0.25

	running = True
	while running:
		# BUGFIX: clock.tick(60) was being called twice per frame (once here, once
		# again at the bottom of the loop). Each call can block to cap the frame
		# rate, so the game was actually running at ~30 real FPS while dt only
		# measured half of that wait - making every animation (selector movement,
		# slashes) take about twice as long in real time as intended, and the
		# input queue (capped at 3) filled up faster than it could drain, so
		# keystrokes typed at a normal pace were silently dropped.
		dt = clock.tick(60) / 1000.0
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				else:
					# queue all key inputs for processing when selector is idle (max 3)
					if len(input_queue) < 3:
						ch = event.unicode.upper()
						if ch and ch in letters:
							input_queue.append(('letter', ch))

		screen.fill((0, 0, 0))

		# animate selector towards target if any (time-based, lerp to match slash duration)
		if target_pos is not None and selector_move_dur > 0.0:
			selector_move_t += dt
			prog = min(1.0, selector_move_t / selector_move_dur)
			selector_pos = selector_start_pos + (target_pos - selector_start_pos) * prog
			if prog >= 1.0:
				# movement finished
				target_pos = None
				selector_move_dur = 0.0
				selector_move_t = 0.0
				# snap selected_index to nearest letter when arrival completes
				# (helps space detection when selector is slightly off due to floats)
				nearest = min(range(n), key=lambda i: selector_pos.distance_to(letter_positions[i]))
				if selector_pos.distance_to(letter_positions[nearest]) <= space_tolerance:
					selected_index = nearest

		# process queued input when selector is idle
		if target_pos is None and input_queue:
			cmd, arg = input_queue.pop(0)
			if cmd == 'letter':
				# handle letter: check if it matches the next letter in the current word
				ch = arg
				current_word = current_words[0]
				missed = False
				if word_progress[0] < len(current_word):
					next_letter = current_word[word_progress[0]].upper()
					if ch == next_letter:
						# correct letter! advance progress
						word_progress[0] += 1
						if word_progress[0] >= len(current_word):
							# word complete! trigger double-slash and get new words
							pending_double = True
							selector_color = blue_color
							# rotate words and reset progress (pick one from each difficulty)
							current_words.pop(0)
							word_difficulties.pop(0)
							diff = random.choice(["easy", "medium", "hard"])
							if diff == "easy":
								current_words.append(random.choice(easy_words))
							elif diff == "medium":
								current_words.append(random.choice(medium_words))
							else:
								current_words.append(random.choice(hard_words))
							word_difficulties.append(diff)
							word_progress.pop(0)
							word_progress.append(0)
					else:
						# BUGFIX: wrong letter - flag it so we can show a red flash.
						# Previously a miss looked identical to a hit (same slash,
						# same color), so mistakes were invisible.
						missed = True
				# always move to the next letter key
				idx = letters.index(ch)
				tx = letter_positions[idx].x
				ty = letter_positions[idx].y
				target_pos = pygame.math.Vector2(int(tx), int(ty))
				selected_index = idx
				if missed:
					miss_flash_t = MISS_FLASH_DUR
				# create a quick slash effect from current selector to target
				if pending_double:
					# primary blue slash
					slashes.append({
						"start": selector_pos.copy(),
						"end": pygame.math.Vector2(int(tx), int(ty)),
						"t": 0.0,
						"dur": slash_dur,
						"color": blue_color,
						"is_blue": True,
					})
					# schedule duplicate to start after the whole lifecycle (dur+hold+fade)
					delay = slash_dur + 0.12 + 0.12
					slashes.append({
						"start": selector_pos.copy(),
						"end": pygame.math.Vector2(int(tx), int(ty)),
						"t": -delay,
						"dur": slash_dur,
						"hold": 0.12,
						"fade": 0.12,
						"color": blue_color,
						"is_blue": True,
					})
					# count blue slashes
					blue_count += 2
					# reset pending flag (affects only next slash)
					pending_double = False
				else:
					slashes.append({
						"start": selector_pos.copy(),
						"end": pygame.math.Vector2(int(tx), int(ty)),
						"t": 0.0,
						"dur": slash_dur,
						# BUGFIX: color a missed letter's slash red instead of the
						# default green, so hits and misses look different.
						"color": red_color if missed else green_color,
					})
				# start a time-based move matching the slash duration
				selector_move_t = 0.0
				selector_move_dur = slash_dur
				selector_start_pos = selector_pos.copy()

		# Draw keyboard keys at the bottom using precomputed positions (QWERTY layout)
		for row in kb_rows:
			for ch in row:
				idx = letters.index(ch)
				pos = letter_positions[idx]
				rect = pygame.Rect(0, 0, square_size, square_size)
				rect.center = (int(pos.x), int(pos.y))
				pygame.draw.rect(screen, (255, 255, 255), rect, 3)
				text_surf = font.render(ch, True, (255, 255, 255))
				text_rect = text_surf.get_rect(center=rect.center)
				screen.blit(text_surf, text_rect)

		# Draw words at the top with difficulty colors
		word_y = 60
		word_spacing = 80
		difficulty_colors = {
			"easy": (144, 200, 100),      # light green
			"medium": (255, 200, 124),    # orange
			"hard": (255, 100, 100)       # light red
		}
		for wi, word in enumerate(current_words):
			word_y_pos = word_y + wi * word_spacing
			difficulty = word_difficulties[wi]
			color = difficulty_colors.get(difficulty, (200, 200, 200))
			# display full word in difficulty color
			word_text = word_font.render(word.upper(), True, color)
			screen.blit(word_text, (100, word_y_pos))
			# show progress (highlight typed letters in green)
			if wi == 0:
				progress = word_progress[0]
				prog_text = word_font.render(word[:progress].upper(), True, (144, 238, 144))
				screen.blit(prog_text, (100, word_y_pos))
			# display difficulty label
			diff_text = word_font.render(f"({difficulty})", True, color)
			screen.blit(diff_text, (100 + len(word) * 30, word_y_pos))

		# BUGFIX: show a brief "MISS" flash near the top when a wrong letter is typed,
		# on top of the slash itself being colored red, for a clearer miss signal.
		if miss_flash_t > 0.0:
			miss_flash_t -= dt
			alpha = max(0, min(255, int(255 * (miss_flash_t / MISS_FLASH_DUR))))
			miss_surf = word_font.render("MISS", True, red_color)
			miss_surf.set_alpha(alpha)
			screen.blit(miss_surf, (w - 160, 30))

		# update and draw slashes on top of squares (with linger and fade)
		if slashes:
			slash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
			to_remove = []
			for si, s in enumerate(slashes):
				s['t'] += dt
				start = s['start']
				end = s['end']
				# skip if scheduled to start later (negative t)
				if s['t'] < 0:
					continue
				# define phases: move -> hold -> fade
				dur = s.get('dur', 0.22)
				hold = s.get('hold', 0.12)
				fade = s.get('fade', 0.12)
				if s['t'] <= dur:
					prog = s['t'] / max(1e-6, dur)
					cur = start + (end - start) * prog
					alpha = 255
					width = max(3, int((1.0 - prog) * 14))
					col = s.get('color', (144, 238, 144))
					pygame.draw.line(slash_surf, (col[0], col[1], col[2], alpha), (int(start.x), int(start.y)), (int(cur.x), int(cur.y)), width)
				elif s['t'] <= dur + hold:
					# full length, hold visible
					alpha = 255
					width = 6
					col = s.get('color', (144, 238, 144))
					pygame.draw.line(slash_surf, (col[0], col[1], col[2], alpha), (int(start.x), int(start.y)), (int(end.x), int(end.y)), width)
				elif s['t'] <= dur + hold + fade:
					# fading out
					fade_t = s['t'] - (dur + hold)
					fade_prog = min(1.0, fade_t / max(1e-6, fade))
					alpha = int(255 * (1.0 - fade_prog))
					width = max(2, int(6 * (1.0 - fade_prog)))
					col = s.get('color', (144, 238, 144))
					pygame.draw.line(slash_surf, (col[0], col[1], col[2], alpha), (int(start.x), int(start.y)), (int(end.x), int(end.y)), width)
				else:
					to_remove.append(si)
			# blit slashes
			screen.blit(slash_surf, (0, 0))
			# remove finished (reverse indices)
			for idx in reversed(to_remove):
				# if removed slash was blue, decrement counter
				ss = slashes[idx]
				if ss.get('is_blue'):
					blue_count -= 1
				del slashes[idx]
			# restore selector color if no active blue slashes
			if blue_count <= 0:
				blue_count = 0
				selector_color = green_color

		# draw selector circle outline on top
		if selector_pos is not None:
			selector_radius = max(12, int(square_size / 2) - 6)
			outline_width = max(4, int(selector_radius * 0.35))
			col = selector_color
			pygame.draw.circle(screen, (col[0], col[1], col[2]), (int(selector_pos.x), int(selector_pos.y)), selector_radius, outline_width)

		pygame.display.flip()
		# BUGFIX: removed the second clock.tick(60) call that used to be here -
		# dt is already measured from the single tick() call at the top of the loop.

	pygame.quit()


if __name__ == "__main__":
	try:
		run()
	except Exception as e:
		print("Error:", e)
		pygame.quit()
		sys.exit(1)

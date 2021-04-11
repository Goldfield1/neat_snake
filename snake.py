import pygame
import neat
import time
import os
import random
import pickle 		
import math
WIN_WIDTH = 400
WIN_HEIGHT = 400

UPDATE_TIME = 300

GEN = 0

class Snake:
	def __init__(self, x, y):
		self.vel = 20
		self.x = x
		self.y = y
		self.dir = "RIGHT"
		self.nodes = [(x,y),(x-20,y),(x-40,y)]
		self.should_grow = False
		#self.should_grow = F

	def move(self):
		# Move head forward, and move all nodes to next node
		if self.dir == "RIGHT":
			self.x += self.vel
		elif self.dir == "LEFT":
			self.x -= self.vel
		elif self.dir == "UP":
			self.y -= self.vel
		else:
			self.y += self.vel

		if self.should_grow:
			self.should_grow = False
			self.nodes.append(self.nodes[-1])

		for x in range(len(self.nodes)-1,0,-1):
			#print(self.nodes)
			self.nodes[x] =  self.nodes[x-1]
		self.nodes[0] = (self.x, self.y)

	def change_direction(self, direction):
		self.direction = direction

	def grow(self):
		self.should_grow = True

	def draw(self, win):
		for node in self.nodes:
			x, y = node
			pygame.draw.rect(win,(0,0,0),(x,y,20,20))
			pygame.draw.rect(win,(0,0,255),(x+1,y+1,18,18))	

class Fruit:
	def __init__ (self, x,y):
		self.x = x
		self.y = y

	def set_location(self, snake):
		locations = [(x,y) for x in range(0,WIN_WIDTH,20) for y in range(0,WIN_HEIGHT,20)]
		for node in snake.nodes:
			x, y = node
			d = locations.remove((x,y))
		self.x, self.y = random.choice(locations)

	def draw(self, win):
		pygame.draw.rect(win,(255,0,0),(self.x,self.y,20,20))		


def draw_window(win, fruit, snake):
	win.fill([0, 0, 0])
	fruit.draw(win)
	snake.draw(win)
	pygame.display.update()

def play_game():
	print("d")
	snake = Snake(20,20)
	fruit = Fruit(380,380)
	for i in range(15):
		snake.grow()
		snake.move()
	#fruit.set_location(snake)

	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	clock = pygame.time.Clock()
	run = True
	update_timer = 0
	latest_move = "RIGHT"
	update_time = UPDATE_TIME
	while run:
		dt = clock.tick(100)
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
			#if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_LEFT:
					if not snake.dir == "RIGHT":	
						latest_move = "LEFT"
				elif event.key == pygame.K_RIGHT:
					if not snake.dir == "LEFT":
						latest_move = "RIGHT"
				elif event.key == pygame.K_UP:
					if not snake.dir == "DOWN":
						latest_move = "UP"
				elif event.key == pygame.K_DOWN:
					if not snake.dir == "UP":
						latest_move = "DOWN"
				if event.type ==pygame.KEYUP:
					if event.key == pygame.K_p:
						if update_time > 100000:
							update_time = UPDATE_TIME
						else:
							update_time = 1000000
					elif event.key == pygame.K_9:
						update_time -= 50
					elif event.key == pygame.K_8:
						update_time += 50
			

			if event.type == pygame.QUIT:
				run = False
				pygame.quit()	
				quit()
		update_timer += dt


		if update_timer > update_time:
			update_timer = 0
			snake.dir = latest_move

			if snake.x >= 400 or snake.x < 0 or snake.y >= 400 or snake.y < 0:
				run = False
				pygame.quit()
				return

			x, y = snake.nodes[0]
			if (x,y) in snake.nodes[1:]:
				run = False
				pygame.quit()
				return

			if (x,y) == (fruit.x, fruit.y):
				print("fruit")
				snake.grow()
				fruit.set_location(snake)

			print(vision(snake,fruit,True))
			
			draw_window(win, fruit, snake)
			snake.move()

def run_game(win, clock_time, update_time, net, draw):
	snake = Snake(180,180)
	fruit = Fruit(180,100)

	clock = pygame.time.Clock()
	run = True
	update_timer = 0
	latest_move = "RIGHT"
	fitness = 0
	ticks_no_fruit = 0
	fruit.set_location(snake)
	moves = []
	while run:
		dt = clock.tick(clock_time)
		for event in pygame.event.get():			
			if event.type == pygame.QUIT:
				run = False
				pygame.quit()	
				quit()
		update_timer += dt

		if update_timer >= update_time:
			update_timer = 0

			# vision of body
			# vision of wall
			output = net.activate((vision(snake,fruit, draw)))
			snake_in = snake.dir
			snake_vision = vision(snake,fruit, draw)

			action = getDirAction(snake, output)
			snake.dir = action

			snake.move()
			ticks_no_fruit += 1
			#fitness += 0.05
			# hitting wall
			if snake.x >= 400 or snake.x < 0 or snake.y >= 400 or snake.y < 0:
				if draw:
					print(output)
					print(snake_in)
					print(snake_vision)
					update_time = 1000000
				else:
					return fitness-40

			# hitting tail
			x, y = snake.nodes[0]
			if (x,y) in snake.nodes[1:]:
				if draw:
					print(output)
					print(snake_in)
					print(snake_vision)
					update_time = 1000000
				else:
					return fitness-50

			# getting fruit
			if (x,y) == (fruit.x, fruit.y):
				ticks_no_fruit = 0
				fitness += 10
				snake.grow()
				fruit.set_location(snake)

			# running in circles
			if ticks_no_fruit > 400:
				return fitness-100

			
			if draw:
				draw_window(win, fruit, snake)

def vision(snake, fruit, draw):
	dirSnack = [-1,-1,-1]
	defaultDist = 600
	dist = [-1,-1,-1] #ahead, left, right
	
	# dist to bodyp
	#print(snake.nodes)
	for i, node in enumerate(snake.nodes[1:]):
		node_x, node_y = node
		if draw:
			#print("HEAD: ", (snake.x, snake.y), "TAIL: ", node)
			pass
		if snake.dir == "RIGHT":
			# distance ahead
			if abs(node_x-snake.x) <= defaultDist and node_y == snake.y and node_x > snake.x:
				if dist[0] == -1 or dist[0] > abs(snake.x-node_x):
					dist[0] = abs(snake.x - node_x + 20)
			# distance left
			if abs(node_y-snake.y) <= defaultDist and node_x == snake.x and node_y < snake.y:
				if dist[1] == -1 or dist[1] > abs(snake.y - node_y):
					dist[1] = abs(snake.y - node_y - 20)
			# distance right
			if abs(node_y-snake.y) <= defaultDist and node_x == snake.x and node_y > snake.y:
				if dist[2] == -1 or dist[2] > abs(snake.y - node_y):
					dist[2] = abs(snake.y - node_y +20) 
		if snake.dir == "LEFT":
			# distance ahead
			if abs(node_x-snake.x) <= defaultDist and node_y == snake.y and node_x < snake.x:
				if dist[0] == -1 or dist[0] > abs(snake.x-node_x):
					dist[0] = abs(snake.x - node_x - 20)
			# distance left
			if abs(node_y-snake.y) <= defaultDist and node_x == snake.x and node_y > snake.y:
				if dist[1] == -1 or dist[1] > abs(snake.y - node_y):
					dist[1] = abs(snake.y - node_y  + 20)
			# distance right
			if abs(node_y-snake.y) <= defaultDist and node_x == snake.x and node_y < snake.y:
				if dist[2] == -1 or dist[2] > abs(snake.y - node_y):
					dist[2] = abs(snake.y - node_y - 20) 
		if snake.dir == "DOWN":
			# distance ahead
			if abs(node_y-snake.y) <= defaultDist and node_x == snake.x and node_y >= snake.y:
				if dist[0] == -1 or dist[0] > abs(snake.y-node_y):
					dist[0] = abs(snake.y - node_y + 20)
			# distance left
			if abs(node_x-snake.x) <= defaultDist and node_y == snake.y and node_x > snake.x:
				if dist[1] == -1 or dist[1] > abs(snake.y - node_y):
					dist[1] = abs(snake.x - node_x + 20)
			# distance right
			if abs(node_x-snake.x) <= defaultDist and node_y == snake.y and node_x < snake.x:
				if dist[2] == -1 or dist[2] > abs(snake.y - node_y):
					dist[2] = abs(snake.x - node_x - 20) 
		if snake.dir == "UP":
			# distance ahead
			if abs(node_y-snake.y) <= defaultDist and node_x == snake.x and node_y < snake.y:
				if dist[0] == -1 or dist[0] > abs(snake.y-node_y):
					dist[0] = abs(snake.y - node_y - 20)
			# distance left
			if abs(node_x-snake.x) <= defaultDist and node_y == snake.y and node_x < snake.x:
				if dist[1] == -1 or dist[1] > abs(snake.y - node_y):
					dist[1] = abs(snake.x - node_x - 20)
			# distance right
			if abs(node_x-snake.x) <= defaultDist and node_y == snake.y and node_x > snake.x:
				if dist[2] == -1 or dist[2] > abs(snake.y - node_y):
					dist[2] = abs(snake.x - node_x + 20) 
		#dist to walls
	wallDist = [-1, -1, -1]  #AHEAD, LEFT, RIGHT
	if snake.dir == "RIGHT":
			wallDist[0] = abs(snake.x - 380)
			wallDist[1] = abs(snake.y)
			wallDist[2] = abs(snake.y - 380)		
	elif snake.dir == "LEFT":
			wallDist[0] = abs(snake.x)
			wallDist[1] = abs(snake.y - 380)
			wallDist[2] = abs(snake.y)
	elif snake.dir == "DOWN":
			wallDist[0] = abs(snake.y - 380)
			wallDist[1] = abs(snake.x - 380)
			wallDist[2] = abs(snake.x)
	elif snake.dir == "UP":			
			wallDist[0] = abs(snake.y)
			wallDist[1] = abs(snake.x)
			wallDist[2] = abs(snake.x - 380)
	if draw:
		print(wallDist)
		print(dist)
		pass

	#ddist = dist.copy()
	for i, distance in enumerate(wallDist):
		if distance < dist[i] or dist[i] == -1:
			dist[i] = distance
			pass

	dirDist = [-1,-1,-1]
	if snake.dir == "RIGHT":
			if snake.y == fruit.y: 
				if snake.x <= fruit.x:
					dirDist[0] = abs(snake.x - fruit.x + 20)
			if snake.x == fruit.x:
				if snake.y <= fruit.y: 
					dirDist[1] = abs(snake.y - fruit.y - 20)
				elif snake.y > fruit.y:
					dirDist[2] = abs(snake.y - fruit.y + 20)
	elif snake.dir == "LEFT":
			if snake.y == fruit.y: 
				if snake.x >= fruit.x:
					dirDist[0] = abs(snake.x - fruit.x - 20)
			if snake.x == fruit.x:
				if snake.y >= fruit.y: 
					dirDist[1] = abs(snake.y - fruit.y + 20)
				elif snake.y < fruit.y:
					dirDist[2] = abs(snake.y - fruit.y - 20)
	elif snake.dir == "DOWN":
			if snake.x == fruit.x: 
				if snake.y <= fruit.y:
					dirDist[0] = abs(snake.y - fruit.y + 20)
			if snake.y == fruit.y:
				if snake.x <= fruit.x: 
					dirDist[1] = abs(snake.x - fruit.x + 20)
				elif snake.x > fruit.x:
					dirDist[2] = abs(snake.x - fruit.x - 20)
	elif snake.dir == "UP":			
			if snake.x == fruit.x: 
				if snake.y >= fruit.y:
					dirDist[0] = abs(snake.y - fruit.y - 20)
			if snake.y == fruit.y:
				if snake.x >= fruit.x: 
					dirDist[1] = abs(snake.x - fruit.x - 20)
				elif snake.x < fruit.x:
					dirDist[2] = abs(snake.x - fruit.x + 20)
	if draw:
		#print(wallDist)
		#print(dist)
		pass
	
	for i, distance in enumerate(dirDist):
		if distance > dist[i]:
			dirDist[i] = -1
			pass
	return dirDist + dist


def getDirAction(snake, output):
    #Calculating which direction is which depending on the current state
    action = "RIGHT"
    if max(output) == output[0]: #LEFT
        if snake.dir == "RIGHT":
            action = "UP"
        elif snake.dir == "LEFT":
            action = "DOWN"
        elif snake.dir == "DOWN":
            action = "RIGHT"
        elif snake.dir == "UP":	
            action = "LEFT"
    elif max(output) == output[1]: #RIGHT
        if snake.dir == "RIGHT":
            action  = "DOWN"
        elif snake.dir == "LEFT":
            action = "UP"
        elif snake.dir == "DOWN":
            action = "LEFT"
        elif snake.dir == "UP":
            action = "RIGHT"
    elif max(output) == output[2]:
    	action = snake.dir

    return action

def fit(genomes, config):
	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	best = 0
	for genome_id, g in genomes:

		net = neat.nn.RecurrentNetwork.create(g, config)
		g.fitness = run_game(win, 30000, 0, net, False)
		#_, gen = genomes[best]
		#if g.fitness > gen.fitness:
		#	best = genome_id

			
def run(config_path):
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
		neat.DefaultSpeciesSet, neat.DefaultStagnation,
		config_path)

	p = neat.Population(config)

	p.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	p.add_reporter(stats)

	#FeedForwardNetwork
	winner = p.run(fit,50)
	net = neat.nn.RecurrentNetwork.create(winner, config)

	with open('winnerFeed', 'wb') as f:
		pickle.dump(net, f)


def run_winner(file):
	win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
	net =  pickle.load( open( file, "rb" ) )
	run_game(win, 50, 10, net, True)

if __name__ == "__main__":
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, "config-rec.txt")
	print(len([1]))
	#run(config_path)
	#run_winner("winnerFeed")
	#play_game()


import pygame
import os
import player
import time
import copy

pygame.init()

WIDTH = 300
HEIGHT = 600
FPS = 60

display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()

class Item:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Consolas", int(height * 0.8))
        self.font_color = (255, 255, 255)
        self.padding = 2
        self.background_color = (90, 90, 90)
        self.line_color = (180, 180, 180)
        self.hidden = False
        self.keywords = []
        
    def render_text(self, text):
        self.text = self.font.render(text, True, self.font_color)

    def fit_width_to_text(self):
        self.width = self.text.get_width() + self.padding * 2
    
    def get_rect(self):
        return (self.x, self.y, self.width, self.height)
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.background_color, self.get_rect())
        pygame.draw.rect(surface, self.line_color, self.get_rect(), 1)

    def onclick(self, structure, x, y):
        pass

class FolderItem(Item):
    def __init__(self, folder, x, y, width, height):
        super().__init__(x, y, width, height)
        self.folder = folder
        self.render_text(str(folder))
        self.fit_width_to_text()
        self.collapsed = False
        self.height_taken = 0

    def collapse(self, structure):
        self.collapsed = True
        self.height_taken = 0
        change = False
        for item in structure.items:
            if item == self:
                change = True
                continue
            if change:
                if type(item) is FileItem and item.file in self.folder.files:
                    item.hidden = True
                    self.height_taken += item.height + structure.item_padding
                #elif type(item) is FolderItem and item.folder in self.folder.subfolders:
                #    item.hidden = True
                #    self.height_taken += item.height + structure.item_padding
                #    if not item.collapsed:
                #        item.collapse(structure)
                else:
                    item.y -= self.height_taken

    def expand(self, structure):
        self.collapsed = False
        change = False
        for item in structure.items:
            if item == self:
                change = True
                continue
            if change:
                if type(item) is FileItem and item.file in self.folder.files:
                    item.hidden = False
                #elif type(item) is FolderItem and item.folder in self.folder.subfolders:
                #    item.hidden = False
                else:
                    item.y += self.height_taken
        self.height_taken = 0

    def onclick(self, structure, x, y):
        super().onclick(structure, x, y)
        if self.collapsed:
            self.expand(structure)
        else:
            self.collapse(structure)
    
    def draw(self, surface):
        super().draw(surface)
        if self.collapsed:
            pygame.draw.rect(surface, self.line_color, (self.x + self.width, self.y, 4, self.height))
        surface.blit(self.text, (self.x + self.padding, self.y + self.height // 2 - self.text.get_height() // 2))

class FileItem(Item):
    def __init__(self, file, x, y, width, height):
        super().__init__(x, y, width, height)
        self.background_color = (255, 90, 90)
        self.file = file
        self.render_text(str(file))
        self.fit_width_to_text()
        player.load(self.file.path)
        self.keywords.append(self.file.name)
    
    def draw(self, surface):
        super().draw(surface)
        surface.blit(self.text, (self.x + self.padding, self.y + self.height // 2 - self.text.get_height() // 2))

    def onclick(self, structure, x, y, button=0):
        super().onclick(structure, x, y)
        if e.button == 3:
            player.add_to_queue(self.file.path)
        elif e.button == 1:
            player.add_to_queue(self.file.path)
            player.play_queue()
        
class Structure:
    def __init__(self, path=None, top_of_screen=0):
        if path is not None:
            self.folder = Folder(path, path)
            self.build(self.folder)
        self.items = []
        self.item_width = 100
        self.item_height = 16
        self.item_padding = 5
        self.item_indentation = 16
        self.scroll_speed = (self.item_height + self.item_padding) * 4
        self.x = 5
        self.y = top_of_screen
        self.top_of_screen = top_of_screen
        if path is not None:
            self.create_items(self.folder)

        #for item in self.items:
        #    if type(item) is FolderItem:
        #        item.collapse(self)

    def __str__(self):
        return self.tree()
    
    def tree(self):
        return self.folder.tree()
    
    def build(self, folder):
        for item in os.listdir(folder.path):
            if "." in item:
                folder.add_file(File(item, "{}/{}".format(folder.path, item)))
            else:
                subfolder = Folder(item, "{}/{}".format(folder.path, item))
                folder.add_subfolder(subfolder)
                self.build(subfolder)

    def create_items(self, folder, position=None):
        print("create items")
        if position is None:
            position = [self.x, self.y]
        for file in folder.files:
            self.items.append(FileItem(file, position[0], position[1], self.item_width, self.item_height))
            self.items[-1].keywords.append(folder.name)
            position[1] += self.item_height + self.item_padding
        for subfolder in folder.subfolders:
            self.items.append(FolderItem(subfolder, position[0], position[1], self.item_width, self.item_height))
            position[0] += self.item_indentation
            position[1] += self.item_height + self.item_padding
            self.create_items(subfolder, position)
            position[0] -= self.item_indentation

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        for item in self.items:
            item.x += dx
            item.y += dy
    
    def handle(self, e):

        if e.type == pygame.MOUSEBUTTONUP:
            
            if e.button == 4:
                if self.y < -self.top_of_screen:
                    self.move(0, self.scroll_speed)
                    
            elif e.button == 5:
                self.move(0, -self.scroll_speed)

            else:
                for item in self.items:
                    x, y = e.pos
                    if x >= item.x and y >= item.y and x <= item.x + item.width and y <= item.y + item.height:
                        if not item.hidden:
                            item.onclick(self, x, y, e.button)
    
    def draw(self, surface):
        for item in self.items:
            if not item.hidden:
                item.draw(surface)

class Folder:
    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.subfolders = []
        self.files = []

    def __str__(self):
        return self.name
    
    def tree(self, indent=4):
        out = " " * max(indent - 4, 0) + str(self) + "\n"
        for file in self.files:
            out += " " * indent + file.name + "\n"
        for folder in self.subfolders:
            out += folder.tree(indent + 4)
        return out
    
    def add_file(self, file):
        self.files.append(file)
    
    def add_subfolder(self, folder):
        self.subfolders.append(folder)

class File:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def __str__(self):
        return self.name
    

class Entry:
    def __init__(self, x, y, width, height, font_size=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = (0, 0, 0)
        if font_size is None:
            self.font_size = self.height
        else:
            self.font_size = font_size
        self.font_family = "Consolas"
        self.set_font()
        self.text = ""
        self.cursor_pos = 0
        self.blink_period = 0.5
        self.set_blinker()
    
    def draw(self, surface):
        if self.show_blinker:
            text = self.text[:self.cursor_pos] + "|" + self.text[self.cursor_pos:]
        else:
            text = self.text
        if self.font is None:
            self.set_font()
        
        pygame.draw.rect(surface, (200, 200, 200), (self.x, self.y, self.width, self.height))
        if text != "":
            text_surface = self.font.render(text, 1, self.color)
            surface.blit(text_surface, (self.x, self.y + self.height // 2 - text_surface.get_height() // 2))
    
    def set_font(self):
        self.font = pygame.font.SysFont(self.font_family, self.font_size)
    
    def set_blinker(self):
        self.show_blinker = True
        self.last_blink = time.time()
    
    def update(self):
        now = time.time()
        if now - self.last_blink >= self.blink_period:
            self.show_blinker = not self.show_blinker
            self.last_blink = now
    
    def handle(self, e):
        
        if e.type == pygame.KEYDOWN:
            
            if e.key == pygame.K_LEFT:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif e.key == pygame.K_RIGHT:
                if self.cursor_pos < len(self.text):
                    self.cursor_pos += 1
            elif e.key == pygame.K_HOME:
                self.cursor_pos = 0
            elif e.key == pygame.K_END:
                self.cursor_pos = len(self.text)
            elif e.key == pygame.K_DELETE:
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
            elif e.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
            elif e.unicode != "":
                self.text = self.text[:self.cursor_pos] + e.unicode + self.text[self.cursor_pos:]
                self.cursor_pos += 1
                
            self.set_blinker()

structure = Structure(input("Folder name: "), top_of_screen=35)
print(structure.tree())

last_string = ""
box = Entry(0, 0, WIDTH, 30, font_size=20)
display_struct = Structure(top_of_screen=35)

while True:

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif e.type == pygame.VIDEORESIZE:
            display = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            box.width = e.w
        box.handle(e)
        if box.text == "":
            structure.handle(e)
        else:
            display_struct.handle(e)
            
    box.update()
    
    if box.text != "" and last_string != box.text:
        last_string = box.text
        x = 5
        y = box.y + box.height + 5
        display_struct.items = []
        for item in structure.items:
            if type(item) is FileItem:
                match = False
                for keyword in item.keywords:
                    if box.text.lower() in keyword.lower():
                        match = True
                        break
                if match:
                    display_struct.items.append(copy.copy(item))
                    display_struct.items[-1].x = x
                    display_struct.items[-1].y = y
                    display_struct.items[-1].hidden = False
                    y += item.height + 5

    display.fill((255, 255, 255))
    if box.text == "":
        structure.draw(display)
    else:
        display_struct.draw(display)
    
    box.draw(display)

    pygame.display.update()
    clock.tick(FPS)


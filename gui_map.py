import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk 
import math
import socket


#  Wymagania systemu: 
#  1. Automatyczne latanie po zadanej ścieżce 
#  2. Obracanie drona na zadane kąty 
#  3. Możliwość nadpisania ścieżki drona w każdym momencie 
#  4. Możliwość w miarę ręcznego sterowania dronem 
#  5. No fly zoney w kształtach koła, prostokątu, 9-kąta wypukłego 


   #Przesya do drona
def send_waypoints_to_backend(waypoints):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 5000)) 
            for lat, lon in waypoints:
                s.sendall(f"{lat},{lon}\n".encode())
            s.sendall(b"END\n")
            print("Punkty wysłane do backendu.")
    except Exception as e:
        print(f"Błąd przesyłania punktów: {e}")

# Dodanie wywołania w odpowiednim miejscu mapy
def execute_mission():
    gps_points = [gui_to_gps(x, y) for x, y in app.path_points]
    send_waypoints_to_backend(gps_points)

def gui_to_gps(self, x, y):
    gps_lat_range = (-35.36098528285018,-35.365998649395)
    gps_lon_range = (149.15914541257442, 149.16778212558168)
    #wymiary zdjęcia mapy
    gui_width = 818
    gui_height = 574
    #pozycja dla drona
    gps_lat = gps_lat_range[0] + (y / gui_height) * (gps_lat_range[1] - gps_lat_range[0])
    gps_lon = gps_lon_range[0] + (x / gui_width) * (gps_lon_range[1] - gps_lon_range[0])
    return gps_lat, gps_lon


class DroneMapApp:
  
   def send_manual_position(self, lat, lon):
    """Wysyła aktualną pozycję drona do backendu """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 5001))
            s.sendall(f"{lat},{lon}\n".encode())
            print(f"Wysłano pozycję ręczną: Lat {lat}, Lon {lon}")
    except Exception as e:
        print(f"Błąd wysyłania pozycji ręcznej: {e}")

   
   

   def update_drone_position(self):
    #Aktualizacja
    
    # Rysowanie nowej pozycji drona na mapie
    self.canvas.coords(self.drone,
                       self.drone_x - self.drone_radius,
                       self.drone_y - self.drone_radius,
                       self.drone_x + self.drone_radius,
                       self.drone_y + self.drone_radius)

    # Rysowanie kierunku drona
    angle_radians = math.radians(self.drone_angle)
    line_length = self.drone_radius * 3  # Długość linii wskazującej kierunek
    end_x = self.drone_x + line_length * math.cos(angle_radians)
    end_y = self.drone_y + line_length * math.sin(angle_radians)

    if hasattr(self, "direction_line"):
        self.canvas.coords(self.direction_line, self.drone_x, self.drone_y, end_x, end_y)
    else:
        self.direction_line = self.canvas.create_line(self.drone_x, self.drone_y, end_x, end_y, arrow=tk.LAST)

    # Aktualizacja informacji
    gps_lat, gps_lon = self.gui_to_gps(self.drone_x, self.drone_y)
    

     #    Przeliczenie na współrzędne GPS
    gps_lat, gps_lon = self.gui_to_gps(self.drone_x, self.drone_y)

     #   Wysłanie danych do backendu
    self.send_drone_position(gps_lat, gps_lon)

     #   Aktualizacja etykiety z informacjami
    self.info_label.config(text=f"Pozycja: ({gps_lat:.6f}, {gps_lon:.6f})")

   def gui_to_gps(self, x, y):
    #wsp. końców mapy
    gps_lat_range = (-35.36098528285018,-35.365998649395)
    gps_lon_range = (149.15914541257442, 149.16778212558168)
    #wymiary zdjęcia mapy
    gui_width = 818
    gui_height = 574
    #pozycja dla drona
    gps_lat = gps_lat_range[0] + (y / gui_height) * (gps_lat_range[1] - gps_lat_range[0])
    gps_lon = gps_lon_range[0] + (x / gui_width) * (gps_lon_range[1] - gps_lon_range[0])
    return gps_lat, gps_lon



   def send_drone_position(self, lat, lon):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', 5001))  # Port do aktualizacji pozycji
                s.sendall(f"{lat},{lon}\n".encode())
                print(f"Wysłano pozycję: Lat {lat}, Lon {lon}")
        except Exception as e:
            print(f"Błąd wysyłania pozycji drona: {e}")
        

   def __init__(self, root):
       self.root = root
       self.root.title("Nawigacja")


       # Ustawienia Canvas
       self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
       self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


       # Dodanie tła do Canvas
       self.map_image = Image.open("/home/vboxuser/Pulpit/Nawigacja/map_background.jpg")  # Wczytaj obraz tła
       self.map_image = self.map_image.resize((818, 574))
       self.map_image_tk = ImageTk.PhotoImage(self.map_image)
       self.canvas.create_image(0, 0, anchor=tk.NW, image=self.map_image_tk)


    # Panel boczny
       self.control_frame = tk.Frame(root, width=200, bg="lightgray")
       self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)

       self.add_controls()

       
       self.path_points = []  #   Punkty trasy
       self.no_fly_zones = []  #  strefy zakazu lotu
       self.drawing_mode = None # tryb rysowania
       self.temp_shape = None  #  Tymczasowe kształty
       self.polygon_points = [] # Punkty dla wielokątów


       
       self.drone_x = 500 #    lok początkowa x
       self.drone_y = 145 #    lok pocz y
       self.drone_angle = 0 #  kąt drona
       self.drone_radius = 5 # rozmiar drona


      #tryb manual
       self.manual_mode = False  # domyślnie wyłączony


       # Rys drona na mapie
       self.drone = self.canvas.create_oval(self.drone_x - self.drone_radius,
                                             self.drone_y - self.drone_radius,
                                             self.drone_x + self.drone_radius,
                                             self.drone_y + self.drone_radius,
                                             fill="blue")


       # Obsługa klawiatury
       self.root.bind("<KeyPress>", self.key_press)


       # Obsługa myszy
       self.canvas.bind("<Button-1>", self.add_point_or_zone)
       self.canvas.bind("<B1-Motion>", self.draw_zone)
       self.canvas.bind("<ButtonRelease-1>", self.finish_drawing)


   def add_controls(self):
       tk.Label(self.control_frame, text="Opcje", bg="lightgray", font=("Arial", 14)).pack(pady=10)


       #reset_button = tk.Button(self.control_frame, text="Resetuj mapę", command=self.reset_map)
       #reset_button.pack(pady=5, fill=tk.X)


       circle_button = tk.Button(self.control_frame, text="Dodaj Okrąg (No-Fly Zone)",
                                  command=lambda: self.set_drawing_mode("circle"))
       circle_button.pack(pady=5, fill=tk.X)


       rect_button = tk.Button(self.control_frame, text="Dodaj Prostokąt (No-Fly Zone)",
                                command=lambda: self.set_drawing_mode("rectangle"))
       rect_button.pack(pady=5, fill=tk.X)


       poly_button = tk.Button(self.control_frame, text="Dodaj Wielokąt (No-Fly Zone)",
                                command=lambda: self.set_drawing_mode("polygon"))
       poly_button.pack(pady=5, fill=tk.X)


       path_button = tk.Button(self.control_frame, text="Dodaj Punkty Trasy",
                               command=lambda: self.set_drawing_mode("path"))
       path_button.pack(pady=5, fill=tk.X)


       end_poly_button = tk.Button(self.control_frame, text="Zakończ Wielokąt",
                                    command=self.finish_polygon)
       end_poly_button.pack(pady=5, fill=tk.X)


       clear_points_button = tk.Button(self.control_frame, text="Usuń punkty trasy",
                                command=self.clear_path_points)
       clear_points_button.pack(pady=5, fill=tk.X)




       #validate_button = tk.Button(self.control_frame, text="czy punkt w fo fly zone", command=self.validate_path)
       #validate_button.pack(pady=5, fill=tk.X)


       reroute_button = tk.Button(self.control_frame, text="Omijaj strefy", command=self.reroute_path)
       reroute_button.pack(pady=5, fill=tk.X)      
       
       auto_fly_button = tk.Button(self.control_frame, text="Lecieć automatycznie",
                                   command=self.fly_automatically)
       auto_fly_button.pack(pady=5, fill=tk.X)

       # Tryb ręczny
       manual_mode_button = tk.Button(self.control_frame, text="Tryb ręczny",
                                      command=self.toggle_manual_mode)
       manual_mode_button.pack(pady=5, fill=tk.X)


       self.info_label = tk.Label(self.control_frame, text="Punkty: 0", bg="lightgray")
       self.info_label.pack(pady=10)

       test_button = tk.Button(self.control_frame, text="Wyślij testową pozycję", command=self.test_send_position)
       test_button.pack(pady=5, fill=tk.X)

   def toggle_manual_mode(self):
    #tryb manual
    self.manual_mode = not self.manual_mode
    if self.manual_mode:
        print("Tryb ręczny włączony")  # Log włączenia trybu ręcznego
        messagebox.showinfo("Tryb Ręczny", "Tryb ręczny aktywowany!")
    else:
        print("Tryb ręczny wyłączony")  # Log wyłączenia trybu ręcznego
        messagebox.showinfo("Tryb Punktów", "Powrót do trybu punktów. Dron wróci na trasę.")









   def key_press(self, event):

    if self.manual_mode:
        if event.keysym == 'w':  # Do przodu
            self.drone_angle = 270
            self.move_drone(0, -5)
        elif event.keysym == 's':  # Do tyłu
            self.drone_angle = 90
            self.move_drone(0, 5)
        elif event.keysym == 'a':  # W lewo
            self.drone_angle = 180
            self.move_drone(-5, 0)            
        elif event.keysym == 'd':  # W prawo
            self.move_drone(5, 0)
            self.drone_angle = 0
        elif event.keysym == 'q':  # Obrót w lewo
            self.drone_angle = (self.drone_angle - 10) % 360
            self.update_drone_position()
        elif event.keysym == 'e':  # Obrót w prawo
            self.drone_angle = (self.drone_angle + 10) % 360
            self.update_drone_position()


   def clear_path_points(self):
    #usuń wszystkie punkty
    self.path_points = []
    self.update_path()
    self.info_label.config(text="Punkty: 0")


   def move_drone(self, dx, dy):
    #tryb manual
    new_x = self.drone_x + dx
    new_y = self.drone_y + dy

    

    if not self.is_in_no_fly_zone(new_x, new_y):
        self.drone_x = new_x
        self.drone_y = new_y
        self.update_drone_position()
    else:
        print("No-Fly Zone")


   def fly_automatically(self):
    #leci po punktu
    if not self.path_points:
        messagebox.showwarning("Brak punktów", "Dodaj punkty do trasy")
        return

    for idx, (x, y) in enumerate(self.path_points):
        self.info_label.config(text=f"Leć do punktu {idx + 1}/{len(self.path_points)}")
        self.move_to_point(x, y)
    messagebox.showinfo("Lot zakończony", "Dron dotarł do wszystkich punktów.")


  
#do usuniecia
   def expand_polygon(self, points, buffer):
    expanded_points = []
    cx = sum(p[0] for p in points) / len(points)  
    cy = sum(p[1] for p in points) / len(points)

    for x, y in points:
        angle = math.atan2(y - cy, x - cx)
        expanded_x = x + buffer * math.cos(angle)
        expanded_y = y + buffer * math.sin(angle)
        expanded_points.append((expanded_x, expanded_y))

    return expanded_points


   def is_in_no_fly_zone(self, x, y):
      for zone in self.no_fly_zones:
          if zone["type"] == "circle":
              cx, cy = zone["center"]
              radius = zone["radius"]
              if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= radius+5:
                  return True
          elif zone["type"] == "rectangle":
              x0, y0, x1, y1 = zone["coords"]
              if x0 <= x <= x1 and y0 <= y <= y1:
                  return True
          elif zone["type"] == "polygon":
              if self.point_in_polygon(x, y, zone["points"]):
                  return True
      return False






   
 # def add_point_or_zone(self, event):
 #     """Dodaje punkt trasy lub strefę """
 #     if self.drawing_mode == "path":
 #         x, y = event.x, event.y
 #         self.path_points.append((x, y))
 #         self.update_path()  # Odświeżenie widoku ścieżki
 #         self.info_label.config(text=f"Punkty: {len(self.path_points)}")
 #     elif self.drawing_mode in ["circle", "rectangle", "polygon"]:
 #         self.start_drawing(event)

   def set_drawing_mode(self, mode):
       """Ustawia tryb rysowania"""
       self.drawing_mode = mode
       self.polygon_points = []  # Resetowanie punktów wielokąta
       if mode == "path":
           messagebox.showinfo("Tryb Rysowania", "Tryb ustawiony na: Dodawanie punktów trasy")
       else:
           messagebox.showinfo("Tryb Rysowania", f"Tryb ustawiony na: Rysowanie {mode.capitalize()}")


   def add_point_or_zone(self, event):
       """Dodaje punkt trasy lub strefę"""
       if self.drawing_mode == "path":
           x, y = event.x, event.y
           self.path_points.append((x, y))
           self.update_path()  # Odświeżenie widoku ścieżki
           self.info_label.config(text=f"Punkty: {len(self.path_points)}")
       elif self.drawing_mode in ["circle", "rectangle", "polygon"]:
           self.start_drawing(event)


   def start_drawing(self, event):
       """ rysowanie strefy zakazu"""
       if self.drawing_mode == "circle":
           self.temp_shape = {"type": "circle", "center": (event.x, event.y), "radius": 0}
           x, y = event.x, event.y
           self.temp_shape["id"] = self.canvas.create_oval(x, y, x, y, outline="red", width=3)
       elif self.drawing_mode == "rectangle":
           self.temp_shape = {"type": "rectangle", "start": (event.x, event.y)}
           x, y = event.x, event.y
           self.temp_shape["id"] = self.canvas.create_rectangle(x, y, x, y, outline="orange", width=3)
       elif self.drawing_mode == "polygon":
           self.polygon_points.append((event.x, event.y))
           if len(self.polygon_points) > 1:
               self.canvas.create_line(self.polygon_points[-2], self.polygon_points[-1], fill="pink", width=3)
           else:
               self.canvas.create_oval(event.x-3, event.y-3, event.x+3, event.y+3, fill="pink")


   def draw_zone(self, event):
       
       if self.drawing_mode == "circle" and self.temp_shape:
           x0, y0 = self.temp_shape["center"]
           x1, y1 = event.x, event.y
           r = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
           self.temp_shape["radius"] = r
           self.canvas.coords(self.temp_shape["id"], x0 - r, y0 - r, x0 + r, y0 + r)
       elif self.drawing_mode == "rectangle" and self.temp_shape:
           x0, y0 = self.temp_shape["start"]
           x1, y1 = event.x, event.y
           self.canvas.coords(self.temp_shape["id"], x0, y0, x1, y1)


   def finish_drawing(self, event):
       """Zakończenie rysowania """
       if self.drawing_mode == "circle" and self.temp_shape:
           self.no_fly_zones.append(self.temp_shape)
           self.temp_shape = None
           messagebox.showinfo("Strefa zakazu lotu", "Okrąg dodany!")
       elif self.drawing_mode == "rectangle" and self.temp_shape:
           x0, y0 = self.temp_shape["start"]
           x1, y1 = event.x, event.y
           self.temp_shape["coords"] = (x0, y0, x1, y1)
           self.no_fly_zones.append(self.temp_shape)
           self.temp_shape = None
           messagebox.showinfo("Strefa zakazu lotu", "Prostokąt dodany!")


   def finish_polygon(self):
       if self.drawing_mode == "polygon" and len(self.polygon_points) > 2:
           poly_id = self.canvas.create_polygon(self.polygon_points, outline="purple", fill="", width=2)
           self.no_fly_zones.append({"type": "polygon", "points": self.polygon_points, "id": poly_id})
           self.polygon_points = []
           messagebox.showinfo("Strefa zakazu lotu", "Wielokąt dodany!")


   def validate_path(self):
       for point in self.path_points:
           x, y = point
           in_no_fly_zone = False


           for zone in self.no_fly_zones:
               if zone["type"] == "circle":
                   cx, cy = zone["center"]
                   radius = zone["radius"]
                   if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= radius:
                       in_no_fly_zone = True


               elif zone["type"] == "rectangle":
                   x0, y0, x1, y1 = zone["coords"]
                   if x0 <= x <= x1 and y0 <= y <= y1:
                       in_no_fly_zone = True


               elif zone["type"] == "polygon":
                   if self.point_in_polygon(x, y, zone["points"]):
                       in_no_fly_zone = True


           if in_no_fly_zone:
               self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="red", outline="red", tags="path")
           else:
               self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="blue", outline="blue", tags="path")


   def reroute_path(self):
       new_path = []
       for point in self.path_points:
           in_no_fly_zone = any(self.check_collision(point, zone) for zone in self.no_fly_zones)
           if in_no_fly_zone:
               point = self.find_safe_point(point) 
           new_path.append(point)
       self.path_points = new_path
       self.update_path()


   def find_safe_point(self, point):
       x, y = point
       for zone in self.no_fly_zones:
           if zone["type"] == "circle":
               cx, cy = zone["center"]
               radius = zone["radius"]
               dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
               if dist < radius:
                   angle = math.atan2(y - cy, x - cx)
                   x = cx + (radius + 10) * math.cos(angle)
                   y = cy + (radius + 10) * math.sin(angle)
       return x, y


   def check_collision(self, point, zone):
       x, y = point
       if zone["type"] == "circle":
           cx, cy = zone["center"]
           radius = zone["radius"]
           return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= radius
       if zone["type"] == "rectangle":
           x0, y0, x1, y1 = zone["coords"]
           return x0 <= x <= x1 and y0 <= y <= y1
       if zone["type"] == "polygon":
           return self.point_in_polygon(x, y, zone["points"])
       return False


   def point_in_polygon(self, x, y, points):
       n = len(points)
       inside = False
       px, py = x, y
       for i in range(n):
           x0, y0 = points[i]
           x1, y1 = points[(i + 1) % n]
           if y0 > py != y1 > py and px < (x1 - x0) * (py - y0) / (y1 - y0) + x0:
               inside = not inside
       return inside

   def move_to_point(self, target_x, target_y, step=2):
   #trub auto
    while True:
        dx = target_x - self.drone_x
        dy = target_y - self.drone_y
        distance = math.sqrt(dx**2 + dy**2)

        if distance < step:  
            self.drone_x = target_x
            self.drone_y = target_y
            self.update_drone_position()
            break

        angle = math.atan2(dy, dx)
        new_x = self.drone_x + step * math.cos(angle)
        new_y = self.drone_y + step * math.sin(angle)

        if self.is_in_no_fly_zone(new_x, new_y):
            angle += math.radians(90)  
           
            new_x = self.drone_x + step * math.cos(angle)
            new_y = self.drone_y + step * math.sin(angle)

        

        self.drone_x = new_x
        self.drone_y = new_y
        self.update_drone_position()
        self.root.update()
        self.root.after(1)

#rysowanie punkty
   def update_path(self):
       self.canvas.delete("path")
       for i, (x, y) in enumerate(self.path_points, start=1):
           self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="yellow", outline="black", tags="path")
           self.canvas.create_text(x + 10, y, text=str(i), fill="white", font=("Arial", 10), tags="path")

   def reset_map(self):
       self.canvas.delete("all")
       self.canvas.create_image(0, 0, anchor=tk.NW, image=self.map_image_tk)
       self.path_points = []
       self.no_fly_zones = []
       self.info_label.config(text="Punkty: 0")
#testowanie 1
   def test_send_position(self, event=None):
        
        # Przykładowa pozycja GPS
        lat, lon = -35,361847112789526, 149.165264
        self.send_drone_position(lat, lon)
        print(f"Wysłano testową pozycję: Lat {lat}, Lon {lon}")




if __name__ == "__main__":
   root = tk.Tk()
   app = DroneMapApp(root)
   root.mainloop()

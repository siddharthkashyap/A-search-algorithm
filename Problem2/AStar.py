import  math, requests, sqlite3, gmplot, webbrowser
import xml.etree.ElementTree as ET

        
class Node():

    def __init__(self, refid,c):
    
        self.ref = refid
        self.parent = None
        self.h = 0
        self.g = 0
        
        c.execute("SELECT * FROM Nodes where RefId={}".format(refid))
        data = c.fetchone()
        self.lat = float(data[1])
        self.lon = float(data[2])
    
    def __eq__(self, other):

        return (self.ref == other.ref)
                   
    def display(self):

        print("Id : {} | (Lat, Lon) : {},{}".format(self.ref, self.lat, self.lon))
        
    def Hdistance(self, other):
        
        R = 6371 * 10**3
        dphi = math.radians(other.lat-self.lat)
        phi1 = math.radians(self.lat)
        phi2 = math.radians(other.lat)
        dlambda = math.radians(other.lon-self.lon)
    
        a = (math.sin(dphi/2))**2 + math.cos(phi1)*math.cos(phi2)*(math.sin(dlambda/2))**2        
        y = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
        d = R*y
    
        return d
        
    def realtime(self, other):
        API_KEY = 'AIzaSyCF-A7KMEyldDY_yLwsXuX_sdkzDCvrlsY'
        res = requests.get(
'''https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&origins='''+str(self.lat)+','+str(self.lon) +
'&destinations=' +str(other.lat) + ',' + str(other.lon) + '&key='+API_KEY)
        json_obj = res.json()
        return json_obj['rows'][0]['elements'][0]['distance']['value']
    

def AStar(initial, goal, vertices, c):

    opened = []
    closed = []
    opened.append(initial)
    while opened != []:
        current = min(opened, key = lambda y: y.g + y.h)
        if(current == goal):
            place = current
            path = [place]
            while place.parent is not None:
                place = place.parent
                path.append(place)
            path.reverse()
            return path
        
        opened.remove(current)
        adjlist = vertices[str(current.ref)] 
        children = []
        for vertexid in adjlist:
            children.append(Node(int(vertexid),c))
          
        for child in children:
            temp = child.Hdistance(current)+current.g   
            if (child not in opened) and (child not in closed):
                child.g = temp
                child.h = child.Hdistance(goal)
                child.parent = current
                opened.append(child)
            if child in opened:
                if child.g > temp:
                    child.g = temp
                    child.parent = current
            if child in closed:
                if child.g > temp:
                    closed.remove(child)
                    child.g = temp
                    child.parent = current
                    opened.append(child)                
        closed.append(current) 
    return []


if __name__ == '__main__':
   
    


    conn = sqlite3.connect("BBox.db")
    cursor= conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS Nodes(RefId REAL, Lat REAL, Lon REAL)")
    
    
    tree = ET.parse('map.osm')
    root = tree.getroot()
    
    vertices = {}
    for node in root.findall('./node'):
        vertices[node.attrib['id']]=0
        cursor.execute("INSERT INTO Nodes VALUES({},{},{})".format(node.attrib['id'],node.attrib['lat'],node.attrib['lon']))
    #conn.commit()

        
    for way in root.findall('./way'):
        valid = 0 
        tags = way.findall('./tag')
        if tags!=[]:
            for tag in tags:
                if (tag.attrib['k']=='highway'):
                    valid = 1
                    break
                    
        if valid == 1:
            waynd = way.findall('./nd')
            waynd = [item.attrib['ref'] for item in waynd]
            
            for i in range(len(waynd)):
                if i == 0:
                    if vertices[waynd[i]] == 0:
                        vertices[waynd[i]]={waynd[i+1]}
                    else:
                        vertices[waynd[i]].add(waynd[i+1])
                elif i == len(waynd)-1:
                    if vertices[waynd[i]] == 0:
                        vertices[waynd[i]]={waynd[i-1]}
                    else:
                        vertices[waynd[i]].add(waynd[i-1])
                else:                  
                    if vertices[waynd[i]] == 0:
                        vertices[waynd[i]]={waynd[i-1],waynd[i+1]}
                    else:
                        vertices[waynd[i]].add(waynd[i-1])
                        vertices[waynd[i]].add(waynd[i+1])
           
    print(len(vertices))          
    Start = Node(2684790802,cursor)
    End = Node( 662739299,cursor) 
    route = AStar(Start, End, vertices,cursor)
    latitude = []
    longitude = []
    if route == []:
        print("Path not found.")
    else:
        for point in route:
            latitude.append(point.lat)
            longitude.append(point.lon)
    
    print("Found a path. Displaying it")
    gmap = gmplot.GoogleMapPlotter(latitude[0], longitude[0], 15)
    gmap.plot(latitude, longitude, '#65C359', edge_width=10)
    gmap.scatter(latitude, longitude, '#FF0000')
    gmap.draw("map.html")
    webbrowser.open("map.html")
    cursor.close()
    conn.close()

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = 'bus_booking_secret'

class Bus:
    def __init__(self):
        self.bus_list = []
        self.seats = {}  # Stores seat matrices for each bus ID
        self.bookings = {}  # Stores booking details for each bus ID

    def add_bus(self, bus_id, route, date, time):
        for bus in self.bus_list:
            if bus['bus_id'] == bus_id:
                return "Bus ID already exists"
        self.bus_list.append({'bus_id': bus_id, 'route': route, 'date': date, 'time': time})
        self.seats[bus_id] = [[0] * 5 for _ in range(10)]  # 10 rows x 5 columns (50 seats)
        return "Bus added successfully"

    def remove_bus(self, bus_id):
        self.bus_list = [bus for bus in self.bus_list if bus['bus_id'] != bus_id]
        self.seats.pop(bus_id, None)
        self.bookings.pop(bus_id, None)
        return "Bus removed successfully"

    def get_buses(self, date=None):
        if date:
            return [bus for bus in self.bus_list if bus['date'] == date]
        return sorted(self.bus_list, key=lambda x: x['date'])

    def book_seats(self, bus_id, bookings, name, phone):
        if bus_id not in self.seats:
            return {"error": "Invalid Bus ID"}
        messages = []
        ticket_info = []
        for row, col in bookings:
            row, col = int(row), int(col)
            if self.seats[bus_id][row][col] == 0:
                self.seats[bus_id][row][col] = 1
                ticket_info.append({"row": row, "col": col})
                self.bookings.setdefault(bus_id, []).append({"name": name, "phone": phone, "row": row, "col": col})
                messages.append(f"Seat ({row}, {col}) successfully booked.")
            else:
                messages.append(f"Seat ({row}, {col}) is already booked.")
        return {"success": messages, "ticket": ticket_info}


bus_system = Bus()

# Sample buses
bus_system.add_bus("101", "Dhaka to Rangpur", "2024-12-01", "10:00 AM")
bus_system.add_bus("102", "Dhaka to Rajshahi", "2024-12-02", "3:00 PM")


@app.route('/')
def home():
    buses = bus_system.get_buses()
    return render_template('index.html', buses=buses)


@app.route('/buses/<date>')
def buses_by_date(date):
    buses = bus_system.get_buses(date=date)
    return render_template('index.html', buses=buses)


@app.route('/seats/<bus_id>')
def seats(bus_id):
    seats = bus_system.seats.get(bus_id)
    if seats is None:
        return jsonify({"error": "Invalid Bus ID"}), 404
    return jsonify({"seats": seats})


@app.route('/book', methods=['POST'])
def book():
    data = request.json  # Receive data as JSON from the frontend
    bus_id = data.get("bus_id")
    bookings = data.get("bookings", [])
    name = data.get("name")
    phone = data.get("phone")

    # Validate input
    if not bus_id or not bookings or not name or not phone:
        return jsonify({"error": "Invalid input. All fields are required."}), 400

    # Book the seats
    result = bus_system.book_seats(bus_id, bookings, name, phone)
    if "error" in result:
        return jsonify({"error": result["error"]}), 400

    # Fetch bus details
    bus_details = next((bus for bus in bus_system.bus_list if bus['bus_id'] == bus_id), None)
    if not bus_details:
        return jsonify({"error": "Bus details not found"}), 404

    # Generate ticket details
    ticket_details = {
        "name": name,
        "phone": phone,
        "bus_id": bus_id,
        "route": bus_details["route"],
        "time": bus_details["time"],
        "seats": result["ticket"]
    }

    return jsonify({"success": result["success"], "ticket": ticket_details})


@app.route('/admin')
def admin_dashboard():
    buses = bus_system.get_buses()
    return render_template('admin.html', buses=buses)


@app.route('/add_bus', methods=['POST'])
def add_bus():
    bus_id = request.form['bus_id']
    route = request.form['route']
    date = request.form['date']
    time = request.form['time']

    if not bus_id or not route or not date or not time:
        return jsonify({"error": "All fields are required"}), 400
    
    result = bus_system.add_bus(bus_id, route, date, time)
    if "already exists" in result:
        return jsonify({"error": result}), 400

    return jsonify({"success": result})


@app.route('/remove_bus/<bus_id>', methods=['POST'])
def remove_bus(bus_id):
    result = bus_system.remove_bus(bus_id)
    return jsonify({"success": result})

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import uuid
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store_monitoring.db'
db = SQLAlchemy(app)


class Store(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    timezone = db.Column(db.String(100), default='America/Chicago')

class ReportData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    store_status_id = db.Column(db.Integer, db.ForeignKey('store_status.id'), nullable=False)
    data = db.Column(db.String(255))

    store = db.relationship('Store', backref=db.backref('report_data', lazy=True))
    store_status = db.relationship('StoreStatus', backref=db.backref('report_data', lazy=True))

# with app.app_context():
#     db.create_all()
#     db.session.commit()


class BusinessHours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time_local = db.Column(db.String(10), nullable=False)
    end_time_local = db.Column(db.String(10), nullable=False)


class StoreStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    timestamp_utc = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(10), nullable=False)


def read_csv_files():
    global store_status_df
    # Read the CSV files into pandas dataframes
    stores_df = pd.read_csv('stores.csv')
    business_hours_df = pd.read_csv('business_hours.csv')

    # Read store status data
    try:
        store_status_df = pd.read_csv('ok.csv', engine='python')
        print('Store status data loaded successfully.')
    except Exception as e:
        print('Error loading store status data:', e)

    # Store the data in the database
    for index, row in stores_df.iterrows():
        store = Store(name=row['store_id'], timezone=row['timezone_str'])
        try:
            with app.app_context():
                db.session.add(store)
                db.session.commit()
        except Exception as e:
            print('Error loading store status data:', e)


    for index, row in business_hours_df.iterrows():
        store_id = row['store_id']
        day_of_week = row['day']
        start_time_local = row['start_time_local']
        end_time_local = row['end_time_local']
        business_hours = BusinessHours(store_id=store_id, day_of_week=day_of_week, start_time_local=start_time_local,
                                       end_time_local=end_time_local)
        with app.app_context():
            db.session.add(business_hours)
            db.session.commit()

    for index, row in store_status_df.iterrows():
        store_id = row['store_id']
        try:
            timestamp_format = '%Y-%m-%d %H:%M:%S.%f %Z'
            timestamp_utc = pd.to_datetime(row['timestamp_utc'], format=timestamp_format)
            print(timestamp_utc)
        except ValueError:
            print(f"Error converting timestamp '{row['timestamp_utc']}' to datetime for row {index}")
            print(row)
            continue

        status = row['status']
        store_status = StoreStatus(store_id=store_id, timestamp_utc=timestamp_utc, status=status)
        with app.app_context():
            db.session.add(store_status)
            db.session.commit()


#read_csv_files()
print("CSV files loaded successfully")


@app.route('/trigger_report', methods=['GET'])
def trigger_report():
    try:
        report_id = str(uuid.uuid4())

        # Get the current date and time in UTC
        current_datetime_utc = pd.Timestamp.utcnow()

        # Get the current day of the week (0 = Monday, 6 = Sunday)
        current_day_of_week = current_datetime_utc.day

        # Get the current time in the local time zone of each store
        stores = Store.query.all()
        for store in stores:
            local_tz = pytz.timezone(store.timezone)
            current_datetime_local = current_datetime_utc.tz_convert(local_tz)
            current_time_local = current_datetime_local.time()

            # Get the business hours for the current day of the week
            business_hours = BusinessHours.query.filter_by(store_id=store.id, day_of_week=current_day_of_week).first()

            if business_hours:
                # If the store is open during business hours, calculate uptime and downtime
                start_time_local = datetime.strptime(business_hours.start_time_local, '%I:%M %p').time()
                end_time_local = datetime.strptime(business_hours.end_time_local, '%I:%M %p').time()

                if current_time_local >= start_time_local and current_time_local <= end_time_local:
                    # Calculate the uptime and downtime for the current hour
                    uptime_last_hour, downtime_last_hour = calculate_uptime_and_downtime(store.id, current_datetime_local - timedelta(hours=1), current_datetime_local)

                    # Calculate the uptime and downtime for the last 24 hours
                    uptime_last_day, downtime_last_day = calculate_uptime_and_downtime(store.id, current_datetime_local - timedelta(hours=24), current_datetime_local)

                    # Calculate the uptime and downtime for the last 7 days
                    uptime_last_week, downtime_last_week = calculate_uptime_and_downtime(store.id, current_datetime_local - timedelta(days=7), current_datetime_local)

                    # Extrapolate uptime and downtime based on business hours and save the report data to the database
                    business_hour_intervals = get_business_hour_intervals(business_hours, current_datetime_local)
                    report_data = []
                    for business_hour_interval in business_hour_intervals:
                        start_time = business_hour_interval[0]
                        end_time = business_hour_interval[1]
                        uptime, downtime = extrapolate_uptime_and_downtime(store.id, start_time, end_time)
                        report_data.append({
                            'store_id': store.id,
                            'report_id': report_id,
                            'uptime(last hour)': uptime_last_hour,
                            'uptime(minute)': uptime,
                            'uptime(last day)': uptime_last_day,
                            'uptime(last week)': uptime_last_week,
                            'downtime(last hour)': downtime_last_hour,
                            'downtime(last minutes)': downtime,
                            'downtime(last day)': downtime_last_day,
                            'downtime(last week)': downtime_last_week,

                            'start_time': start_time,
                            'end_time': end_time
                        })

                    with app.app_context():
                        report_data_json = jsonify({'report_id': report_id, 'store_id': store.id, 'data': report_data})
                        report_data_db = ReportData(report_id=report_id, data=report_data_json)
                        db.session.add(report_data_db)
                        db.session.commit()
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)

    # Return the report_id to the client
    response = jsonify({"report_id": report_id})
    return response




@app.route('/get_report/<report_id>', methods=['GET'])
def get_report(report_id):
    # Check if the report exists in the database
    report_data = ReportData.query.filter_by(report_id=report_id).all()
    if not report_data:
        return jsonify({'error': 'Invalid report ID'})

    # Check the status of the report
    report_status = ReportStatus.query.filter_by(report_id=report_id).first()
    if not report_status:
        return jsonify({'error': 'Report status not found'})

    if report_status.status == 'running':
        # If report generation is not complete, return "Running"
        return jsonify({'status': 'Running'})
    else:
        # If report generation is complete, generate the CSV file and return it
        store_ids = list(set([data.store_id for data in report_data]))
        csv_data = []
        for store_id in store_ids:
            store_data = [data for data in report_data if data.store_id == store_id]
            if not store_data:
                continue
            store = Store.query.filter_by(id=store_id).first()
            business_hours = BusinessHours.query.filter_by(store_id=store_id, day_of_week=datetime.utcnow().weekday()).first()
            if not business_hours:
                continue
            start_time = datetime.strptime(business_hours.start_time, '%I:%M %p').time()
            end_time = datetime.strptime(business_hours.end_time, '%I:%M %p').time()
            total_time = (datetime.combine(date.min, end_time) - datetime.combine(date.min, start_time)).total_seconds() / 60.0
            uptime_last_hour = sum([data.uptime_last_hour for data in store_data if data.timestamp >= business_hours.start_time_utc and data.timestamp < business_hours.end_time_utc])
            downtime_last_hour = sum([data.downtime_last_hour for data in store_data if data.timestamp >= business_hours.start_time_utc and data.timestamp < business_hours.end_time_utc])
            uptime_last_day = sum([data.uptime_last_day for data in store_data if data.timestamp >= datetime.utcnow() - timedelta(hours=24)])
            downtime_last_day = sum([data.downtime_last_day for data in store_data if data.timestamp >= datetime.utcnow() - timedelta(hours=24)])
            uptime_last_week = sum([data.uptime_last_week for data in store_data if data.timestamp >= datetime.utcnow() - timedelta(days=7)])
            downtime_last_week = sum([data.downtime_last_week for data in store_data if data.timestamp >= datetime.utcnow() - timedelta(days=7)])
            csv_data.append([store_id, uptime_last_hour, uptime_last_day / 60.0, uptime_last_week / 60.0, downtime_last_hour, downtime_last_day / 60.0, downtime_last_week / 60.0])

        # Write the CSV data to a file
        with open(f'{report_id}.csv', 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week'])
            writer.writerows(csv_data)

        # Update the report status in the database
        report_status.status = 'complete'
        report_status.completed_timestamp = datetime.utcnow()
        db.session.commit()

        # Return the CSV file to the client
        response = make_response(send_file(f'{report_id}.csv', as_attachment=True))
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={report_id}.csv'
        return response





if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)


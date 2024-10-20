# -*- coding: utf-8 -*-
"""Employee Email.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Wixg-0hu5ENd7z5NXceTvkttFcKDY8OA
"""

# Imports
import getpass
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.colab import files
import io
import csv
from datetime import datetime

## Allows access to google drive

# Import Google libraries
import gspread
from google.colab import auth
from oauth2client.client import GoogleCredentials
from google.auth import default

# Authenticate and create a client
auth.authenticate_user()
creds, _ = default()
gc = gspread.authorize(creds)

# Open the Google Sheets file
spreadsheet = gc.open("Aggregated Data").sheet1

# 'worksheet' object, fetching the data
data = spreadsheet.get_all_values()

# Put that data into a Pandas dataframe
Employee_df = pd.DataFrame(data[1:], columns=data[0])

# Convert Hours and Activity sums to floats
Employee_df['Hours'] = pd.to_numeric(Employee_df['Hours'], errors='coerce').astype(float)
Employee_df['activity_sums'] = pd.to_numeric(Employee_df['activity_sums'], errors='coerce').astype(float)

# Display the result
#Employee_df

# Prompt the user to upload a CSV file
print("Please upload a CSV file with your list of recepients:")
uploaded = files.upload()

# Get the filename and content of the uploaded file
for filename, content in uploaded.items():
  # Read the CSV file into a Pandas DataFrame
  df = pd.read_csv(io.BytesIO(content))

# Display the result
#df

"""Research
Research for others

Clinic Hrs
"""

# Get unique employee titles
unique_titles = Employee_df['Employee Title'].unique()

# Display options to the user
print("Available Employee Titles:")
for i, title in enumerate(unique_titles):
    print(f"{i+1}. {title} \n")

# Get user input
while True:
    try:
        selected_option = int(input("Enter the number of the desired Employee Title: "))
        if 1 <= selected_option <= len(unique_titles):
            selected_title = unique_titles[selected_option - 1]
            break
        else:
            print("Invalid option. Please enter a number from the list.")
    except ValueError:
        print("Invalid input. Please enter a number.")

# Filters the dataframe by the user entered title
Filtered_df = Employee_df[Employee_df['Employee Title'] == selected_title]

# Dictionary of filtered activites by employee title
activity_mapping = {
    "Clinician": ["DBQs and IMOs", "Clinic Hrs", ""],
    "Researcher": ["Research", "Research for others", ""],
    "Scheduler": ["DBQs and IMOs", "Scheduling", ""]
    "Historian": ["DBQs and IMOs", ""]
    # Add more mappings for other employee titles
}

# Get activities for the title
allowed_activities = activity_mapping.get(selected_title, [])

# Filter the dataframe to only the activities allowed for the selected title
Filtered_df = Filtered_df[Filtered_df['Activity Name'].isin(allowed_activities)]

# Display the result
Filtered_df

# Convert the Entry Date to datetime format so it can be filtered
Filtered_df['Entry Date'] = pd.to_datetime(Filtered_df['Entry Date'], format='%d-%b-%y')

# Gets user input for the start date of the report
start_date = input("Enter the date to start this report (YYYY-MM-DD): ")

# Gets user input for the end date of the report
end_date = input("Enter the date to end this report (YYYY-MM-DD): ")
print(f"You entered: {start_date} - {end_date}")

# Filters the report based on the user entered start date
Filtered_df = Filtered_df[Filtered_df['Entry Date'] >= pd.to_datetime(start_date)]

# Filters the report based on the user entered end date
Filtered_df = Filtered_df[Filtered_df['Entry Date'] <= pd.to_datetime(end_date)]

# Display the result
#Filtered_df

# Group by 'User Name' and sum 'Hours' and 'activity_sums'
grouped_df = Filtered_df.groupby(['User Name', 'Employee Title']).agg({'Hours': 'sum', 'activity_sums': 'sum'})

# Calculate the average by dividing the sums
grouped_df['average_activity_hours'] = grouped_df['activity_sums'] / grouped_df['Hours']

# Display the result
grouped_df

# Sort the DataFrame by 'average_activity_hours' in descending order
sorted_df = grouped_df.sort_values(by=['average_activity_hours'], ascending=False)

# Reset the index and assign a new index starting from 1
sorted_df = sorted_df.reset_index()
sorted_df['Rank'] = sorted_df['average_activity_hours'].rank(method='min', ascending=False).astype(int)

# Display the result
#sorted_df.head(10)

# Email credentials (replace with your actual credentials)

# sender_email = input("Enter your Email: ")
sender_email = ''

#sender_password = getpass.getpass(prompt='Enter your pasword: ')
sender_password = ''

#Define a function to send an email using SMTPlib
def send_email(receiver_email, subject, body):

  message = MIMEMultipart()
  message['From'] = sender_email
  message['To'] = receiver_email
  message['Subject'] = subject
  message.attach(MIMEText(body, 'plain'))

  try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()
    print(f"Email sent to {receiver_email}")
  except Exception as e:
    print(f"Error sending email to {receiver_email}: {e}")

#Finds the max value of the rank column
max_value = sorted_df['Rank'].max()

# Ask the user to verify the start date, end date, and employee title
print(f"You are about to send emails to the uploaded list of people\n\nPlease verify the following details:")
print(f"  Start Date: {start_date}")
print(f"  End Date: {end_date}")
print(f"  Employee Title: {selected_title}")

verification = input("\nAre these details correct? (y/n): ")

if verification.lower() == 'y':
    # Continue with the script
    print("Continuing...")
else:
    # Cancel execution of the script
    print("Script execution canceled.")
    sys.exit()

# Create a list to store the output of the send email for loop
output_data = []

# Iterates through the dataframe the user uploaded and sends an email to each user with their stats
for index, row in df.iterrows():
  name = row['name']
  if name in sorted_df['User Name'].values:
    data = sorted_df[sorted_df['User Name'] == name]
    subject = f"Rank Update - {selected_title}s"
    body = f"""Hello {name},

This is a computer generated email:

Your average activities per hour are {data['average_activity_hours'].values[0]:.2f} and your current rank is {data['Rank'].values[0]} out of {max_value} {selected_title}s during the period beginning on {start_date} and ending on {end_date}.

Thanks,

Steve N."""

    send_email(row['email'], subject, body)
    output_data.append([name, "Email sent", body.replace("\n"," ")])  # Store successful email info

  else:
    print(f"{name} is not in the source report and will not receive an email.")
    output_data.append([name, "Not in report", "N/A"])  # Store info for skipped users

# Write the output to a CSV file
now = datetime.now()
csv_filename = f"Email_Results-{selected_title}s-{now}.csv"

with open(csv_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Name", "Status", "Content"])  # Write header row
    writer.writerows(output_data)  # Write output data

# Make the CSV file downloadable
files.download(csv_filename)

# Display the resulting email text
# output_data

from secrets import EMAIL_ADDRESS, EMAIL_PASSWORD
from bs4 import BeautifulSoup
import requests
import smtplib
from email.message import EmailMessage
import time


def main():
    CRN = input("Please enter the CRN: ")
    # The link that contains capacity info about the course
    course_link = f"https://suis.sabanciuniv.edu/prod/bwckschd.p_disp_detail_sched?term_in=202101&crn_in={CRN}"

    user_emails = input(
        "Please enter emails that you want to be notified (seperated by space): ")
    # List of contacts which the notification/email will be sent to
    contacts = [x for x in user_emails.split(" ") if x]

    # Sending an initial GET Request to get the course details
    response = requests.get(course_link, timeout=20)
    soup = BeautifulSoup(response.content, "html5lib")
    while(soup.find("table", summary="This table is used to present the detailed class information.") == None):
        CRN = input(
            "No course with matching CRN does not exist, please enter the correct CRN: ")
        course_link = f"https://suis.sabanciuniv.edu/prod/bwckschd.p_disp_detail_sched?term_in=202101&crn_in={CRN}"
        response = requests.get(course_link, timeout=20)
        soup = BeautifulSoup(response.content, "html5lib")

    msg = EmailMessage()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = contacts

    # Example course details: Computer Networks (Course) - 10547 (Course CRN) - CS 408 (Course name/code)- 0 (Course section)
    course_details = [x.strip() for x in soup.find(
        "table", summary="This table is used to present the detailed class information.").tbody.tr.th.text.split("-")]

    # 4 items in course_details if it's a lecture section: Computer Networks - 10547 - CS 408 - 0
    if len(course_details) == 4:
        course_name, course_section, course_CRN = course_details[
            2], course_details[3], course_details[1]

    # 5 items in course_details if it's a lab/recitation section: Computer Networks - Lab - 10549 - CS 408L - A
    elif len(course_details) == 5:
        course_name, course_section, course_CRN = course_details[
            3], course_details[4], course_details[2]

    # Main loop for checking if a course has free seats available every 5 seconds, break the loop if there are remaining seats
    loop_count = 0

    while True:
        print(
            f"Loop: {loop_count} | {time.strftime('%H:%M:%S', time.localtime())}")

        try:
            response = requests.get(course_link, timeout=20)
            soup = BeautifulSoup(response.content, "html5lib")

            # Example seating numbers: 90 (Capacity) - 60 (Actual) - 30 (Remaining)
            seating_numbers = soup.find("table", summary="This layout table is used to present the seating numbers.").tbody.find_all("tr")[
                1].find_all("td", class_="dddefault")

            # If the capacity and actual number of students are not equal (i.e. there are free seats available)
            if seating_numbers[0].text != seating_numbers[1].text:
                msg["Subject"] = f"{course_name} - {course_section} - {course_CRN}, FREE SEAT AVAILABLE"
                msg.set_content(
                    f"There are free seats available for {seating_numbers[2].text} student(s).")

                try:
                    # Send an email to notify the contacts
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                        smtp.send_message(msg)

                    print("Email sent.")

                except Exception as e:
                    print("An error occured while sending the email. Details:")
                    print(e)

                break

        except:
            # Sometimes there can be random GET Request errors
            print(
                f"Loop: {loop_count} FAILED: Error during GET Request. Trying again.")

        loop_count += 1

        # For our purposes, there is no need for time.sleep() as it takes 5 seconds to get a response from the course link,
        # but time.sleep() may be used when there is a need to slow down the loop
        # time.sleep(5)


if __name__ == "__main__":
    main()

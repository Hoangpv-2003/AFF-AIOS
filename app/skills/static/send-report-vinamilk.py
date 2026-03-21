def send_report(input_data):
    """
    Sends an email with a summary of the results and any associated images.

    Parameters:
    - input_data: A dictionary containing the results and recipient information.
        - 'results': A list of result items, each expected to have 'title' and 'content'.
        - 'recipient': The email address of the recipient.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage

    # Extract inputs
    results = input_data.get("results")
    recipient = input_data.get("recipient")
    if not results or not recipient:
        raise ValueError("Missing required input: 'results' or 'recipient'")

    # Generate summary text
    summary_text = "Tóm tắt thông tin:\n"
    for result in results[:3]:  # Limit to top 3 results
        title = result.get("title", "N/A")
        content = result.get("content", "N/A")
        summary_text += f"- {title}: {content[:100]}...\n"

    # Prepare email
    msg = MIMEMultipart()
    msg["From"] = "no-reply@example.com"
    msg["To"] = recipient
    msg["Subject"] = "Báo cáo kết quả"

    # Attach summary text
    msg.attach(MIMEText(summary_text, "plain"))

    # Attach images (if any)
    for result in results:
        image_data = result.get("image")
        if image_data:
            image = MIMEImage(image_data)
            image.add_header("Content-Disposition", "attachment", filename="image.png")
            msg.attach(image)

    # Send the email
    try:
        with smtplib.SMTP("smtp.example.com", 587) as server:
            server.starttls()
            server.login("user@example.com", "password")
            server.sendmail(msg["From"], [recipient], msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
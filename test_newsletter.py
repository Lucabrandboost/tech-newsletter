from newsletter_generator import NewsletterGenerator

def test_newsletter():
    newsletter = NewsletterGenerator()
    try:
        print("Sending newsletter...")
        newsletter.send_newsletter()
        print("Newsletter sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_newsletter() 
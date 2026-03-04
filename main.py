import requests
import time
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict


# Request statistics tracker
class RequestStats:
    def __init__(self):
        self.data = []
        self.endpoint_counts = defaultdict(int)
        self.method_counts = defaultdict(int)
        self.status_counts = defaultdict(int)
        self.response_times = []

    def log(self, endpoint, method, status, response_time):
        self.data.append(
            {
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "response_time": response_time,
            }
        )
        self.endpoint_counts[endpoint] += 1
        self.method_counts[method] += 1
        self.status_counts[str(status)[0] + "xx"] += 1
        self.response_times.append(response_time)

    def report(self):
        print("\n--- Request Statistics ---")
        print("Total requests per endpoint:")
        for ep, count in self.endpoint_counts.items():
            print(f"  {ep}: {count}")
        print("Requests per HTTP method:")
        for m, count in self.method_counts.items():
            print(f"  {m}: {count}")
        print("Response status distribution:")
        for s, count in self.status_counts.items():
            print(f"  {s}: {count}")
        if self.response_times:
            avg = sum(self.response_times) / len(self.response_times)
            print(f"Average response time: {avg:.3f}s")
            print(
                f"Fastest: {min(self.response_times):.3f}s, Slowest: {max(self.response_times):.3f}s"
            )
        else:
            print("No requests made.")

    def visualize(self):
        if not self.data:
            print("No data to visualize.")
            return
        # Endpoint counts
        plt.figure(figsize=(10, 6))
        sns.barplot(
            x=list(self.endpoint_counts.keys()), y=list(self.endpoint_counts.values())
        )
        plt.title("Requests per Endpoint")
        plt.ylabel("Count")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
        # Method distribution
        plt.figure(figsize=(6, 4))
        sns.barplot(
            x=list(self.method_counts.keys()), y=list(self.method_counts.values())
        )
        plt.title("Requests per HTTP Method")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.show()
        # Response times
        plt.figure(figsize=(8, 4))
        sns.histplot(self.response_times, bins=10, kde=True)
        plt.title("Response Time Distribution")
        plt.xlabel("Seconds")
        plt.tight_layout()
        plt.show()


stats = RequestStats()


# 1. Get users by city
def get_users_by_city(city):
    url = "https://jsonplaceholder.typicode.com/users"
    params = {"address.city": city}
    start = time.time()
    resp = requests.get(url, params=params)
    elapsed = time.time() - start
    stats.log(url, "GET", resp.status_code, elapsed)
    users = resp.json()
    found = False
    for user in users:
        if user.get("address", {}).get("city", "").lower() == city.lower():
            print(f"{user['name']} - {user['email']}")
            found = True
    if not found:
        print("No users found in that city.")


# 2. Create a new post
def create_post():
    url = "https://jsonplaceholder.typicode.com/posts"
    # Get all posts to check for title
    start = time.time()
    resp = requests.get(url)
    elapsed = time.time() - start
    stats.log(url, "GET", resp.status_code, elapsed)
    posts = resp.json()
    userId = input("Enter userId: ")
    while True:
        title = input("Enter post title: ")
        if any(post["title"].lower() == title.lower() for post in posts):
            print("Title already exists. Please choose another.")
        else:
            break
    body = input("Enter post body: ")
    payload = {"userId": userId, "title": title, "body": body}
    start = time.time()
    resp = requests.post(url, json=payload)
    elapsed = time.time() - start
    stats.log(url, "POST", resp.status_code, elapsed)
    print("Response:", resp.json())


# 3. Update a post
def update_post():
    postId = input("Enter postId to update: ")
    url = f"https://jsonplaceholder.typicode.com/posts/{postId}"
    choice = input("Update title, body, or both? (t/b/both): ").strip().lower()
    data = {}
    if choice == "t":
        data["title"] = input("New title: ")
    elif choice == "b":
        data["body"] = input("New body: ")
    elif choice == "both":
        data["title"] = input("New title: ")
        data["body"] = input("New body: ")
    else:
        print("Invalid choice.")
        return
    headers = {"Authorization": "fake-token-12345"}
    start = time.time()
    resp = requests.patch(url, json=data, headers=headers)
    elapsed = time.time() - start
    stats.log(url, "PATCH", resp.status_code, elapsed)
    print("Updated post:", resp.json())


# 4. Delete a post
def delete_post():
    while True:
        postId = input("Enter postId to delete: ")
        url = f"https://jsonplaceholder.typicode.com/posts/{postId}"
        start = time.time()
        resp = requests.delete(url)
        elapsed = time.time() - start
        stats.log(url, "DELETE", resp.status_code, elapsed)
        if resp.status_code == 200:
            print("Post deleted successfully.")
            break
        else:
            print(f"Deletion failed (status {resp.status_code}). Try again.")


# 5. Statistics and Analysis


def main():
    while True:
        print("\nChoose an option:")
        print("1. Get users by city")
        print("2. Create a new post")
        print("3. Update a post")
        print("4. Delete a post")
        print("5. Show statistics")
        print("6. Visualize statistics")
        print("0. Exit")
        choice = input("Enter choice: ")
        if choice == "1":
            city = input("Enter city name: ")
            get_users_by_city(city)
        elif choice == "2":
            create_post()
        elif choice == "3":
            update_post()
        elif choice == "4":
            delete_post()
        elif choice == "5":
            stats.report()
        elif choice == "6":
            stats.visualize()
        elif choice == "0":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()

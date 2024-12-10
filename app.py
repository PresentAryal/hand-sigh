import os
import csv
import copy
import cv2 as cv
import numpy as np
import mediapipe as mp

from model.keypoint_classifier.keypoint_classifier import KeyPointClassifier

datasetdir = "model/dataset/dataset 1"

def main():
    cap = cv.VideoCapture(0)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 960)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 540)

    hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )
    classifier = KeyPointClassifier()

    with open("model/keypoint_classifier/keypoint_classifier_label.csv", encoding="utf-8-sig") as f:
        labels = [row[0] for row in csv.reader(f)]

    mode = 0

    while True:
        key = cv.waitKey(10)
        if key == 27: break  # ESC
        if key == 100: mode = 2  # 'd': Dataset mode

        ret, frame = cap.read()
        if not ret: break

        frame = cv.flip(frame, 1)
        debug_img = process_frame(frame, hands, classifier, labels, mode)

        cv.imshow("Hand Gesture Recognition", debug_img)

        if mode == 2:
            process_dataset(hands, classifier)
            mode = 0
            print("Dataset processing complete.")

    cap.release()
    cv.destroyAllWindows()

def process_frame(frame, hands, classifier, labels, mode):
    image = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    results = hands.process(image)
    debug_img = copy.deepcopy(frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            brect, landmarks = calculate_landmarks(debug_img, hand_landmarks)
            normalized = preprocess_landmarks(landmarks)
            hand_sign_id = classifier(normalized)

            debug_img = draw_landmarks(debug_img, landmarks)
            debug_img = draw_info_text(debug_img, brect, labels[hand_sign_id])

    return debug_img

def calculate_landmarks(image, hand_landmarks):
    h, w = image.shape[:2]
    landmarks = [[int(pt.x * w), int(pt.y * h)] for pt in hand_landmarks.landmark]
    x, y, w, h = cv.boundingRect(np.array(landmarks))
    return [x, y, x + w, y + h], landmarks

def preprocess_landmarks(landmarks):
    base_x, base_y = landmarks[0]
    normalized = [(x - base_x, y - base_y) for x, y in landmarks]
    max_val = max(max(abs(x), abs(y)) for x, y in normalized)
    return [coord / max_val for point in normalized for coord in point]

def draw_landmarks(image, landmarks):
    for i, point in enumerate(landmarks):
        cv.circle(image, tuple(point), 5 if i == 0 else 3, (255, 255, 255), -1)
    return image

def draw_info_text(image, brect, label):
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)
    cv.putText(image, label, (brect[0] + 5, brect[1] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return image

def process_dataset(hands, classifier):
    for i, folder in enumerate(os.listdir(datasetdir)):
        for img_name in os.listdir(os.path.join(datasetdir, folder)):
            img_path = os.path.join(datasetdir, folder, img_name)
            img = cv.imread(img_path)
            results = hands.process(cv.cvtColor(img, cv.COLOR_BGR2RGB))
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    _, landmarks = calculate_landmarks(img, hand_landmarks)
                    normalized = preprocess_landmarks(landmarks)
                    logging_csv(i, normalized)
    print("Dataset processed.")

def logging_csv(label, data):
    with open("model/keypoint_classifier/keypoint.csv", "a", newline="") as f:
        csv.writer(f).writerow([label, *data])

if __name__ == "__main__":
    main()

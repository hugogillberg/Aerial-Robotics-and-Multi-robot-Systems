# defines a YOLO detection result

# class probability
int32 class_id
string class_name
float64 score

# ID for tracking
string id

# 2D bounding box surrounding the object in pixels
yolo_import/BoundingBox2D bbox

# 3D bounding box surrounding the object in meters
yolo_import/BoundingBox3D bbox3d

# segmentation mask of the detected object
# it is only the boundary of the segmented object
yolo_import/Mask mask

# keypoints for human pose estimation
yolo_import/KeyPoint2DArray keypoints

# keypoints for human pose estimation
yolo_import/KeyPoint3DArray keypoints3d

bash
#!/bin/bash
while true; do
# Stage any changes or new files
git add -A# Only commit and push if there is actually something new
if ! git diff-index --quiet HEAD --; then
git commit -m "Auto-update: $(date)"
git push origin main
fi# Wait 5 seconds before checking the folder again
sleep 5
done

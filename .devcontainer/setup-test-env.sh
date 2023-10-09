echo "Preparing ./test-dotenv/"
echo "Copying files from docs"
cp --recursive --no-clobber docs/devcontainer-test-dotenv/. test-dotenv || exit 1
file_list="test-dotenv/test-mysql.env test-dotenv/test-postgres.env test-dotenv/test-sqlite-file.env test-dotenv/test-sqlite-memory.env"
# Healthchecks UUID
echo "Setting IPGET_TEST_HEALTHCHECK_UUID from local environment: $IPGET_TEST_HEALTHCHECK_UUID"
sed --in-place 's/<YOUR IPGET_TEST_HEALTHCHECK_UUID>/'"$IPGET_TEST_HEALTHCHECK_UUID"'/g' $file_list
# Discord Webhook
echo "Setting IPGET_TEST_DISCORD_WEBHOOK from local environment: $IPGET_TEST_DISCORD_WEBHOOK"
sed --in-place 's@<YOUR IPGET_TEST_DISCORD_WEBHOOK>@'"$IPGET_TEST_DISCORD_WEBHOOK"'@g' $file_list
echo "Finished preparing ./test-dotenv/"

This file has been deprecated and its content moved into `README.md`.

The integration no longer refers to a "12h forecast"; the component exposes a time-stamped "Forecast" sensor. See `README.md` for up-to-date documentation and examples.

Additional sections are constantly being added as more areas are covered by monitoring.

## Usage Examples

### Automations

```yaml
automation:
  - alias: "Alert on poor road conditions"
    trigger:
      platform: state
      entity_id: sensor.e18_current_conditions
      to:
        - "Snowing heavily"
        - "Icy"
    action:
      service: notify.mobile_app
      data:
        message: "Poor conditions on E18!"
```

### Template Sensors

```yaml
template:
  - sensor:
      - name: "Road Status"
        unique_id: road_status
        state: "{{ state_attr('sensor.e18_current_conditions', 'reliability') }}%"
```

### Dashboard Card

Use the Entities card or a custom template card to display road conditions:

```yaml
type: entities
entities:
  - entity: sensor.e18_current_conditions
  - entity: sensor.e18_forecast
title: Road Conditions
```

## Data Update Interval

By default, road condition data is updated every 5 minutes. To modify this, you can edit the `UPDATE_INTERVAL` constant in `const.py` (value in seconds).

## Troubleshooting

### "Cannot Connect" Error During Setup

**Symptoms**: Integration shows "Cannot connect" error when adding integration.

**Solutions**:
1. **Check Home Assistant logs**: Go to Settings → System → Logs and search for `digitraffic_road` to see detailed error messages
2. **Verify internet connection**: Ensure your Home Assistant instance has internet access
3. **Check API availability**: The integration uses mock data by default for compatibility
4. **Restart Home Assistant**: Sometimes a restart resolves temporary connection issues
5. **Check firewall**: Ensure no firewall is blocking connections to digitraffic.fi

### Entities Not Showing Data

**Symptoms**: Sensors appear but show "Unknown" or no state.

**Solutions**:
1. **Enable debug logging**: Add this to your configuration.yaml:
   ```yaml
   logger:
     logs:
       custom_components.digitraffic_road: debug
   ```
2. **Check Home Assistant logs**: Look for any errors related to the integration
3. **Verify section ID**: Make sure the road section ID is correct
4. **Wait for first update**: Data may take up to 5 minutes to appear initially

### Integration Not Appearing in Add Integration

**Solutions**:
1. **Restart Home Assistant**: New integrations may not appear until a restart
2. **Clear browser cache**: Your browser may be caching old integration lists
3. **Check HACS installation**: Verify the integration files are in `custom_components/digitraffic_road/`
4. **Check file permissions**: Ensure files are readable by the Home Assistant process

## Debug Logging

To enable detailed debug logging for troubleshooting:

1. Add to your `configuration.yaml`:
   ```yaml
   logger:
     logs:
       custom_components.digitraffic_road: debug
   ```

2. Restart Home Assistant
3. Check Settings → System → Logs for `digitraffic_road` entries
4. Look for lines like:
   - "Fetching road sections"
   - "Updating data for section"
   - "Error fetching road sections"

These logs will help identify where the issue is occurring.

## Support

For issues, feature requests, or contributions, please visit:
https://github.com/EightEFI/Digitraffic-road-conditions/issues

## License

See the LICENSE file for details.

## Disclaimer

This integration is not affiliated with the Finnish Transport Infrastructure Agency (Väylävirasto). The data is provided as-is from the Digitraffic API. Use at your own discretion for informational purposes.

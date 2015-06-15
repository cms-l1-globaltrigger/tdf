% rebase('index.tpl', title='TDF WebControl')

<style>
table tr {
    border: 1px solid #333;
    background-color: #eee;
}
table td {
    border: 0;
}
</style>

<h3>Crate Status</h3>

<p>Crate: {{crate_name}}</p>

<table>
  <tr>
    <th>Device ID</th>
    <th>Slot</th>
    <th>Type</th>
    <th>Status</th>
    <th>L1Menu</th>
  </tr>
  % for device in devices:
  <tr>
    <td>{{device.device}}</td>
    <td>{{device.slot}}</td>
    <td>{{device.type}}</td>
    <td style="color:{{{0:'red', 1:'green', 2:'orange', 3:'red'}.setdefault(device.state, 'black')}};">{{device.state_str}}</td>
    <td>{{device.l1menu if hasattr(device, 'l1menu') else ''}}</td>
  </tr>
  % end
</table>

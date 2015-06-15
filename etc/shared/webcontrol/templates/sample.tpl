% rebase('index.tpl', title='TDF WebControl')
<h3>Device: {{device}}</h3>

<ul>
  % for filename in filenames:
    <li>{{filename}}</li>
  % end
</ul>

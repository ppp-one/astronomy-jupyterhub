import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  ABCWidgetFactory,
  DocumentRegistry,
  DocumentWidget
} from '@jupyterlab/docregistry';
import { PageConfig, URLExt } from '@jupyterlab/coreutils';
import { Widget } from '@lumino/widgets';

const FACTORY = 'FITS Viewer';
const FILE_TYPE = 'fits';

/** Build the URL of the served viewer page for a given file path. */
function viewerUrl(path: string): string {
  const base = URLExt.join(
    PageConfig.getBaseUrl(),
    'fits-lab-extension',
    'static',
    'viewer.html'
  );
  return base + '?path=' + encodeURIComponent(path);
}

/** A document widget that hosts the FITS viewer in an isolated iframe. */
class FitsViewerWidget extends Widget {
  private _iframe: HTMLIFrameElement;
  private _path: string;

  constructor(context: DocumentRegistry.Context) {
    super();
    this.addClass('jp-FitsViewer');
    this._path = context.path;

    this._iframe = document.createElement('iframe');
    this._iframe.style.width = '100%';
    this._iframe.style.height = '100%';
    this._iframe.style.border = 'none';
    this._iframe.setAttribute(
      'sandbox',
      'allow-scripts allow-same-origin allow-popups'
    );
    this._iframe.src = viewerUrl(this._path);
    this.node.appendChild(this._iframe);

    // Reload the image when the file changes on disk.
    context.fileChanged.connect(() => {
      const win = this._iframe.contentWindow;
      if (win) {
        win.postMessage({ command: 'loadPath', path: this._path }, '*');
      }
    });
  }
}

class FitsWidgetFactory extends ABCWidgetFactory<
  DocumentWidget<FitsViewerWidget>
> {
  protected createNewWidget(
    context: DocumentRegistry.Context
  ): DocumentWidget<FitsViewerWidget> {
    const content = new FitsViewerWidget(context);
    const widget = new DocumentWidget({ content, context });
    return widget;
  }
}

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'fits-lab-extension:plugin',
  description: 'View FITS images in the JupyterLab file browser.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    app.docRegistry.addFileType({
      name: FILE_TYPE,
      displayName: 'FITS Image',
      extensions: ['.fits', '.fit'],
      mimeTypes: ['application/fits'],
      contentType: 'file',
      fileFormat: 'base64'
    });

    const factory = new FitsWidgetFactory({
      name: FACTORY,
      modelName: 'base64',
      fileTypes: [FILE_TYPE],
      defaultFor: [FILE_TYPE],
      readOnly: true
    });

    app.docRegistry.addWidgetFactory(factory);
  }
};

export default plugin;

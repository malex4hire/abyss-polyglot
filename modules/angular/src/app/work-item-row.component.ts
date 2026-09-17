import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  reflectComponentType,
} from "@angular/core";
import { WorkItem } from "../lib/types";

/**
 * A component that declares its own dependencies.
 *
 * standalone: true means no NgModule. What the template needs is listed in imports on
 * the component itself, so the unit of compilation is the component rather than a module
 * declaring a set of them. That removes the indirection where a template failed because
 * a directive was declared in a module nobody remembered to import.
 */
@Component({
  selector: "app-work-item-row",
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <li data-testid="row">
      <button type="button" (click)="select.emit(item.id)">{{ item.title }}</button>
      <span data-testid="row-status">{{ item.status }}</span>
      <span [attr.data-priority]="item.priority">{{ item.priority }}</span>
    </li>
  `,
})
export class WorkItemRowComponent {
  @Input({ required: true }) item!: WorkItem;
  @Output() select = new EventEmitter<string>();

  /**
   * What this component declares about itself, read back through the public reflection
   * API rather than from a comment.
   *
   * standalone: true means there is no NgModule. Everything the template uses is listed
   * in imports on the component itself, so the unit of compilation is the component
   * rather than a module declaring a set of them, which removes the indirection where a
   * template failed because a directive was declared in a module nobody imported.
   *
   * The decorator is data attached to the class, and reflectComponentType is how the
   * framework and its tooling read it. Inputs and outputs come from the same place,
   * which is why a parent's template binding can be checked at compile time.
   */
  describeSelf(): { selector: string; standalone: boolean; inputs: string[] } {
    const mirror = reflectComponentType(WorkItemRowComponent);
    return {
      selector: mirror?.selector ?? "",
      standalone: mirror?.isStandalone ?? false,
      inputs: (mirror?.inputs ?? []).map((input) => input.propName),
    };
  }
}
